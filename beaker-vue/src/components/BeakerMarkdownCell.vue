<template>
    <div
        class="markdown-cell"
        @dblclick.stop.prevent="if (!editing && !props.markdown_readonly) {editing = true};"
        @keyup.enter.exact.stop.prevent="if (!editing && !props.markdown_readonly) {editing = true;}; focusEditor();"
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
                        v-model="cell.source"
                        placeholder="Your markdown..."
                        :extensions="codeExtensions"
                        :autofocus="true"
                        language="markdown"
                    />
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps, ref, inject, computed, onBeforeMount, defineExpose, nextTick} from "vue";
import { marked } from 'marked';
import { Codemirror } from "vue-codemirror";
import { oneDark } from '@codemirror/theme-one-dark';
import { markdown } from '@codemirror/lang-markdown';
import { EditorView } from '@codemirror/view';

const props = defineProps([
    "cell",
    "markdown_readonly"
]);


const cell = ref(props.cell);
const theme = inject('theme');
const editing = ref(false);
const editorRef = ref(null);

const codeExtensions = computed(() => {
    const ext = [
        markdown(),
        EditorView.lineWrapping,
    ];

    if (theme.value === 'dark') {
        ext.push(oneDark);
    }
    return ext;

});

const focusEditor = () => {
    const editor: HTMLElement|null = editorRef?.value?.querySelector('.cm-content');
        if (editor) {
            editor.focus();
        }
};



const renderedMarkdown = computed(() => {
    return marked.parse(props.cell?.source);
});

const execute = () => {
    editing.value = false;
}

const enter = (evt?: KeyboardEvent) => {
    if (props.markdown_readonly) {
        return;
    }
    editing.value = true;
    if (typeof(evt) !== "undefined") {
        evt.preventDefault();
        evt.stopPropagation();
    }
}

defineExpose({
    execute,
    enter,
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
