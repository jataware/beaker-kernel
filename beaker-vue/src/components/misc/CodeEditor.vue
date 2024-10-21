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
import { defineProps, defineModel, ref, defineEmits, defineExpose, shallowRef, computed, withDefaults, inject } from "vue";
import { Codemirror } from "vue-codemirror";
import { EditorView } from "codemirror";
import { Extension } from "@codemirror/state";
import { python } from "@codemirror/lang-python";
import { r } from 'codemirror-lang-r';
import { markdown } from "@codemirror/lang-markdown";
import { oneDark } from "@codemirror/theme-one-dark";
import { json } from "@codemirror/lang-json";
import { javascript } from "@codemirror/lang-javascript";
import { julia } from "@plutojl/lang-julia";
import { IBeakerTheme } from '../../plugins/theme';

declare type DisplayMode = "light" | "dark";
declare type Language = "python" | "julia" | "markdown" | "json" | "javascript" | string;

const languageMap: {[key: string]: (options: any) => Extension} = {
    python,
    python3: python,
    python2: python,
    julia,
    markdown,
    json,
    javascript,
    rlang: r,
    r,
    ir: r,
}

declare interface Props {
    displayMode: DisplayMode,
    language?: Language,
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

const extensions = computed<Extension[]>(() => {
    const enabledExtensions: Extension[] = [
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
    if(props.language !== undefined) {
        enabledExtensions.push(
            languageMap[props.language](props.languageOptions)
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
})

</script>

<style lang="scss">

</style>
