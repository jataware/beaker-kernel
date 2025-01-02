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
import { Extension, Prec } from "@codemirror/state";
import { oneDark } from "@codemirror/theme-one-dark";
import { LanguageSupport } from "@codemirror/language";
import { autocompletion, completionKeymap, completionStatus, selectedCompletion, acceptCompletion, closeCompletion } from "@codemirror/autocomplete";
import { IBeakerTheme } from '../../plugins/theme';
import { BeakerLanguage, LanguageRegistry, getCompletions } from "../../util/autocomplete";
import { BeakerSession } from 'beaker-kernel/src';

const session: BeakerSession = inject('session');

declare type DisplayMode = "light" | "dark";

declare interface Props {
    displayMode: DisplayMode,
    language?: string,
    languageOptions?: any,
    modelValue: string,

    autofocus?: boolean,
    disabled?: boolean,
}

const props = withDefaults(defineProps<Props>(), {
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
    const filteredCompletionKeymap = completionKeymap.filter(item => !['Tab', 'Escape'].includes(item.key));
    const overriddenKeymap = [
        ...filteredCompletionKeymap,
        {key: "Tab", run: (editorView) => {
            const state = editorView.state;
            const selection = state.selection.main;
            const lineStartRegex = new RegExp("^\\s*$", "m");
            const endOfWordRegex = new RegExp("^\\w(\\b|$)","m");
            if (completionStatus(state) === "active" && selectedCompletion(state) !== null) {
                return acceptCompletion(editorView);
            }
            if (selection.empty && endOfWordRegex.test(state.sliceDoc(selection.to - 1, selection.to + 1))) {
                return true;

            }
            // Don't indent cursor isn't a in the middle of a line
            if (selection.empty && !lineStartRegex.test(state.sliceDoc(0, selection.to))) {
                return true;
            }


            return false;
        }},
        // Prevent escape key from exiting cell editing if autocomplete is cancelled by pressing exec.
        {
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
