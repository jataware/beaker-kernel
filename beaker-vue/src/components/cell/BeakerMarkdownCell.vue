<template>
    <div class="markdown-cell"
        @dblclick="enter()"
    >
        <div v-if="!editing" v-html="renderedMarkdown"></div>
        <div v-else>
            <div class="markdown-edit-cell-grid">
                <div
                    class="markdown-edit-data"
                    :class="{'dark-mode': theme === 'dark'}"
                    :ref="editorRef"
                >
                    <Codemirror
                        v-model="editorContents"
                        placeholder="Your markdown..."
                        :ref="codeMirrorRef"
                        :extensions="codeExtensions"
                        :autofocus="false"
                        language="markdown"
                        @ready="handleReady"
                    />
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps, ref, inject, computed, nextTick, onBeforeMount, defineExpose, getCurrentInstance, shallowRef} from "vue";
import { marked } from 'marked';
import { Codemirror } from "vue-codemirror";
import { markdown } from '@codemirror/lang-markdown';
import { EditorView } from '@codemirror/view';
import { findSelectableParent } from '@/util';

const props = defineProps([
    "cell"
]);


const instance = getCurrentInstance();
const cell = ref(props.cell);
const theme = inject('theme');
const editing = ref(false);
const editorRef = ref(null);
const codeMirrorRef = ref(null);
const codeMirrorEditorView = shallowRef();
const codeMirrorEditorState = shallowRef();
const editorContents = ref<string>(cell.value.source);

const codeExtensions = computed(() => {
    const ext = [
        markdown(),
        EditorView.lineWrapping,
    ];

    return ext;

});

const handleReady = ({view, state}) => {
    // See vue codemirror api/npm docs: https://codemirror.net/docs/ref/
    codeMirrorEditorView.value = view;
    codeMirrorEditorState.value = state;
};

const renderedMarkdown = computed(() => {
    return marked.parse(props.cell?.source);
});

const execute = () => {
    editing.value = false;
    cell.value.source = editorContents.value;
}

const enter = () => {
    editing.value = true;

    nextTick(() => {
        if(codeMirrorEditorView.value?.focus) {
            codeMirrorEditorView.value?.focus();
        }
    });
}

const exit = () => {
    let target: HTMLElement = (instance.vnode.el as HTMLElement);
    const selectableParent = findSelectableParent(target);
    selectableParent?.focus();
}

const clear = () => {
    cell.value.source = "";
}

defineExpose({
    execute,
    enter,
    exit,
    clear,
});

onBeforeMount(() => {
    marked.setOptions({
       gfm: true,
       sanitize: false,
       langPrefix: `language-`,
     });
})

</script>

<style lang="scss">

.markdown-cell {
    padding-right: 2rem;
    padding-left: 1rem;
    min-height: 80%;
}

.markdown-edit-cell-grid {
    display: grid;

    grid-template-areas:
        "code code code";

    grid-template-columns: 1fr 1fr 1fr auto;
}

.markdown-edit-data {
    grid-area: code;
    background-color: var(--surface-a);
    // white-space: pre-wrap;

    .cm-editor {
        border: 1px solid var(--surface-d);
        // white-space: pre-wrap;
    }
    .cm-focused {
        outline: none;
        border: 1px solid var(--purple-200);
    }
    &.dark-mode {
        .cm-focused {
            border-color: #5b3c5b;
        }
    }
}

</style>
