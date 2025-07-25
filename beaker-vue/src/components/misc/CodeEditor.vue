<template>
    <Codemirror
        v-model="model"
        :extensions="extensions"
        :disabled="props.disabled"
        :autofocus="props.autofocus"
        @ready="handleReady"
        @update:modelValue="modelUpdate"
    />
</template>

<script setup lang="ts">
import { ref, shallowRef, computed, inject, withDefaults } from "vue";
import { Codemirror } from "vue-codemirror";
import { EditorView, keymap } from "@codemirror/view";
import { EditorState, Prec, type Extension } from "@codemirror/state";
import { oneDark } from "@codemirror/theme-one-dark";
import type { LanguageSupport } from "@codemirror/language";
import { autocompletion, completionKeymap, completionStatus, selectedCompletion, acceptCompletion, closeCompletion, startCompletion } from "@codemirror/autocomplete";
import { Diagnostic, linter, lintGutter, forceLinting, setDiagnostics } from "@codemirror/lint";
import type { IBeakerTheme } from '../../plugins/theme';
import { type BeakerLanguage, LanguageRegistry, getCompletions } from "../../util/autocomplete";
import { BeakerSession } from 'beaker-kernel';

const session: BeakerSession = inject('session');

declare type DisplayMode = "light" | "dark";

export interface CodeEditorProps {
    displayMode?: DisplayMode,
    language?: string,
    languageOptions?: any,
    modelValue: string,

    autofocus?: boolean,
    disabled?: boolean,
    readonly?: boolean,
    annotations?: any[],
}

const props = withDefaults(defineProps<CodeEditorProps>(), {
    displayMode: "light",
    autofocus: false,
    disabled: false,
    annotations: () => [],
});

const model = ref<string>(props.modelValue);

const emit = defineEmits([
        'submit',
        "update:modelValue",
]);
const { theme, toggleDarkMode } = inject<IBeakerTheme>('theme');

const annotationCategories = ref<Map<string, {}>>(new Map());

const codeMirrorView = shallowRef<EditorView>();
const codeMirrorState = shallowRef();

const handleReady = ({view, state}) => {
    // See vue codemirror api/npm docs: https://codemirror.net/docs/ref/
    codeMirrorView.value = view;
    codeMirrorState.value = state;
};

const modelUpdate = (newValue: string): void => {
    emit("update:modelValue", newValue);
}

const displayMode = computed<DisplayMode>(() => {
    if (theme.mode === 'default') {
        return 'light';
    }
    else {
        return theme.mode;
    }
});

const extensions = computed(() => {
    // Remove tab and esc keybindings from default CM keymapping.
    const filteredCompletionKeymap = completionKeymap.filter(item => !['Tab', 'Escape'].includes(item.key));
    // Override default CM keymapping the keys.
    const overriddenKeymap = [
        ...filteredCompletionKeymap,
        {key: "Tab", run: (editorView: EditorView) => {
            const editorState = editorView.state;
            const selection = editorState.selection.main;

            const startLine = editorState.doc.lineAt(selection.from);
            const firstNonWhitespaceOffset = startLine.text.match(/\S|$/)?.index || 0;
            const inStartingWhitespace = (
                selection.from >= startLine.from
                && selection.from <= startLine.from + firstNonWhitespaceOffset
            );

            // If an autocomplete is active and something is selected, accept the completion.
            if (completionStatus(editorState) === "active" && selectedCompletion(editorState) !== null) {
                return acceptCompletion(editorView);
            }

            // Only indent if cursor or selection is at start of line
            if (inStartingWhitespace) {
                // Returning false allows default action (indentation)
                return false;
            }

            // Default to starting an autocompletion, if possible.
            startCompletion(editorView);

            // Prevent default action
            return true;
        }},
        // Prevent escape key from exiting cell editing if autocomplete is cancelled by pressing exec.
        {
            // Using built-in helper "any" so we have access to the original keyboard event to allow stopping
            // propagation, preventing blurring the node when cancelling an autocompletion via the escape key.
            any(editorView: EditorView, event: KeyboardEvent) {
                if (event.key === "Escape") {
                    const state = editorView.state;
                    if (completionStatus(state) === "active") {
                        event.stopImmediatePropagation();
                        event.stopPropagation();
                        event.preventDefault();
                        closeCompletion(editorView);
                    }
                    return true;
                }
                return false;
            },
        }
    ];

    const enabledExtensions: Extension[] = [
        // Keymapping
        Prec.highest(keymap.of(overriddenKeymap)),
        EditorState.readOnly.of(props.readonly ?? false),
        EditorView.lineWrapping,
        [EditorView.theme({
            '.cm-scroller': {
                fontFamily: "'Ubuntu Mono', 'Courier New', Courier, monospace",
            }
        })],
    ];
    if (displayMode.value === "dark") {
        enabledExtensions.push(oneDark);
    }


    const language: BeakerLanguage = LanguageRegistry.get(props.language);

    const autocompleteOptions = autocompletion({
        override: [(completion) => getCompletions(completion, session)],
        defaultKeymap: false,
        activateOnCompletion: language?.activateOnCompletion,
    });
    enabledExtensions.push(autocompleteOptions);

    if(language !== undefined) {
        const languageSupport: LanguageSupport = language.initializer(props.languageOptions);
        enabledExtensions.push(
            languageSupport,
        )
    }

    if(props.annotations?.length) {
        const linterAnnotations = linter((view) => {
            return props.annotations.map(annotation => {
                const category_id = annotation.issue.category?.id ?? "default"
                if (annotation.issue?.category && !annotationCategories.value.has(annotation.issue.category.id)) {
                    annotationCategories.value.set(annotation.issue.category.id, annotation.issue.category);
                }
                const className = `category-${category_id} icon-${annotation.issue.category?.icon ?? "default"}`;
                const diagnostic = {
                    from: annotation.start,
                    to: annotation.end,
                    severity: annotation.issue.severity,
                    message: annotation.title_override ?? annotation.issue.title,
                    markClass: className,
                    source: category_id,
                    // color: annotation.issue.category?.color,
                    // icon: annotation.issue.category?.icon ?? undefined,
                    renderMessage() {
                        const el = document.createElement('div');
                        const description = annotation.message_override || annotation.issue.description;
                        const extraMessage = annotation.message_extra ? `<p>${annotation.message_extra}</p>` : '';
                        el.innerHTML = `<h4 style="margin: 0.2rem 0">${annotation.title_override || annotation.issue.title}</h4>`;
                        el.innerHTML += `<p>${description}</p>`;
                        if(extraMessage) {
                            el.innerHTML += `<p>${extraMessage}</p>`;
                        }
                        return el;
                    },
                }
                if (annotation.link) {
                    diagnostic["actions"] = [{
                        name: "Learn More",
                        apply: () => window.open(annotation.link, '_blank')
                    }]
                }
                return diagnostic;
            });
        });
        enabledExtensions.push(linterAnnotations);
        enabledExtensions.push(lintGutter({
            hoverTime: 200,
        }));
    }
    return enabledExtensions;
});

const focus = () => {
    codeMirrorView.value?.focus();
}

const blur = () => {
    codeMirrorView.value?.contentDOM?.blur();
}

defineExpose({
    focus,
    blur,
    view: codeMirrorView,
    update: modelUpdate,
    model: model
})

</script>

<style lang="scss">
    .cm-completionIcon-instance {
        &::after {
            content: '𝑥';
        }
    }

.cm-diagnostic {
    white-space: normal;
}

// for gutter markers
.cm-gutter-lint {
    width: 1.6em;

    // marker container
    .cm-lint-marker {
        padding: 0.2em 0;
    }

    .cm-lint-marker-error {

        content: ""; /* clear the default content which requires an svg */
        position: relative;

        &::before {
            // content: "\e90b"; /* unicode for pi-times icon */
            // content: "";   // pasting pi-times-circle from website, but below is better
            // content: "\e90c"; /* unicode for pi-times-circle icon */
            content: ""; /* character for pi-exclamation-circle icon */
            font-family: 'PrimeIcons';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: rgb(236, 77, 77);
            font-size: 0.9rem;
        }
    }

    .cm-lint-marker-warning {
        content: ""; /* clear the default content which requires an svg */
        position: relative;

        &::before {
            font-family: 'PrimeIcons';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 0.9rem;
            color: #ff9800;
            content: ""; // exclamation triangle char
        }

    }

    .cm-lint-marker-info {

        content: ""; /* clear the default content which requires an svg */
        position: relative;

        &::before {
            font-family: 'PrimeIcons';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 0.9rem;
            color: #2196f3;
            content: ""; // exclamation triangle char
        }
    }
}

//  z-index > 99 is higher than the sidemenu drag handle, etc
.cm-tooltip-hover {
    z-index: 99 !important;
}

// decent max-size for long sentences, longer vertical
// content will scroll instead of overflowing out of the container
.cm-tooltip {
    max-width: 60vw;
    overflow-y: auto;
    // white on light mode looks better than default gray
    background-color: var(--p-surface-0) !important;

    padding: 1rem !important;

    // and override for dark theme/mode
    [data-theme="dark"] & {
        background-color: var(--p-surface-b) !important;
    }
}

// style tooltips
.cm-tooltip.cm-tooltip-lint {
    border: 1px solid #ddd;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);

    ul {
        margin: 0;
        padding: 0;
    }
}

:root {
    --color: 255, 0, 0;
}

.cm-lintRange {
    background-image: none !important;
    text-decoration: underline wavy rgba(var(--color), 0.5) !important;
    text-decoration-skip-ink: none;

    &.category-literal {
        --color: #FFFF00;
        background-color: color-mix(in srgb, var(--color) 20%, transparent);
    }

    &.category-assumptions {
        background-color: rgba(#FFCC22, 0.1);
    }

    &.category-grounding {
        background-color: rgba(#FF0000, 0.1);
    }

    &.category-grounding.category-literal {
        background-color: rgba(#00FF00, 0.1);
    }
}

</style>
