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
import { defineProps, ref, defineEmits, defineExpose, shallowRef, computed, withDefaults, inject } from "vue";
import { Codemirror } from "vue-codemirror";
import { EditorView, keymap } from "@codemirror/view";
import { EditorState, Extension, Prec } from "@codemirror/state";
import { oneDark } from "@codemirror/theme-one-dark";
import { LanguageSupport } from "@codemirror/language";
import { autocompletion, completionKeymap, completionStatus, selectedCompletion, acceptCompletion, closeCompletion, startCompletion } from "@codemirror/autocomplete";
import { IBeakerTheme } from '../../plugins/theme';
import { BeakerLanguage, LanguageRegistry, getCompletions } from "../../util/autocomplete";
import { BeakerSession } from 'beaker-kernel/src';
import { linter, Diagnostic, lintGutter } from "@codemirror/lint";

const ANNOTATION_TYPES = {
    logic_error: {
        "id": "logic_error",
        "display": "Potential Logical Error",
        "color": "#FF0012",
        "message_table": {
            "fallacy_1": {
                "title": "You made a boo-boo!",
                "description": "Here's why you're so dumb!",
                "severity": "major",
                "link": "https://lmgtfy.com/"
            },
            "average_of_averages": {
                "title": "Potential averaging of averages",
                "description": "Potential averaging of a list of averages",
                "severity": "warning",
                "link": "https://wikipedia.org/wiki/Common_errors_in_statistical_analysis"
                }
            }
    },
    assumptions: {
        "id": "assumptions",
        "display": "Assumptions in code",
        "color": "#AA8888",
        "severity": "info",
        "message_table": {
            "assumption_in_algorithm": {
                "title": "Assumption in algorithm",
                "description": "The following assumption was made in this algorithm:\n",
                "link": "https://lmgtfy.com/"
            },
            "assumption_in_value": {
                "title": "Assumption in value",
                "description": "The following assumption was made with regards to the value of this variable:\n",
                "link": "https://lmgtfy.com/"
            }
        }
    }
}

const MOCK_ANNOTATIONS = [
    {
        "start": 0,  // Character, not line
        "end": 19,
        "error_type": "logic_error",
        "error_id": "fallacy_1",
        // "title_override": "",
        // "message_override": "",
        "message_extra": "", 
    },
    {
        "start": 138,  // Character, not line
        "end": 181,
        "error_type": "assumptions",
        "error_id": "assumption_in_value",
        "message_extra": "Value is assumed to always be positive.", 
    }
]

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
}

const props = withDefaults(defineProps<CodeEditorProps>(), {
    displayMode: "light",
    autofocus: false,
    disabled: false,
});

const model = ref<string>(props.modelValue);

const emit = defineEmits([
        'submit',
        "update:modelValue",
]);
const { theme, toggleDarkMode } = inject<IBeakerTheme>('theme');

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


    const myLinter = linter(view => {
        return MOCK_ANNOTATIONS.map(annotation => {
            const annotationType = ANNOTATION_TYPES[annotation.error_type];
            const messageInfo = annotationType.message_table[annotation.error_id];
            
            return {
                from: annotation.start,
                to: annotation.end,
                severity: "error", // messageInfo.severity,
                message: messageInfo.title,
                // Rich HTML description with clickable link
                renderMessage() {
                    const el = document.createElement('div');
                    el.innerHTML = `
                    <div>
                        <h4 style="margin: 0px;">${messageInfo.title}</h4>
                        <p style="margin: 0px;">${messageInfo.description} <a href="${messageInfo.link}" target="_blank">Learn more</a>
                        </p>
                    </div>
                    `;
                    return el;
                },
                // optional add actions that appear as buttons
                // actions: [{
                //     name: "Learn More",
                //     apply: () => window.open(messageInfo.link, '_blank')
                // }]
            } as Diagnostic;
        });
    });

    enabledExtensions.push(myLinter);
    enabledExtensions.push(lintGutter({
        // Customize hover delay (default is 300ms)
        hoverTime: 200,
        
        // Optional: Filter which diagnostics show markers
        markerFilter: (diagnostics) => {
            // Example: only show markers for errors and warnings
            return diagnostics.filter(d => 
                d.severity === "error" || d.severity === "warning"
            );
        },

        // Optional: Filter which diagnostics show in tooltips
        // tooltipFilter: (diagnostics) => {
        //     // You could show different information in the tooltip
        //     // than what shows in the gutter
        //     return diagnostics;
        // }
    }));


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

</style>
