<template>
    <div
        class="markdown-cell"
        @dblclick.stop.prevent="if (!editing) {editing = true};"
    >
        <div v-if="!editing" v-html="renderedMarkdown"></div>
        <div v-else>
            <div class="markdown-edit-cell-grid">
                <div
                    class="markdown-edit-data"
                    :class="{'dark-mode': theme === 'dark'}"
                >
                    <Codemirror
                        v-model="cellSource"
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
    "cell"
]);


const cell = ref(props.cell);
const theme = inject('theme');
const editing = ref(false);
const cellSource = ref<string>(props.cell?.source.join("\n"));

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

const renderedMarkdown = computed(() => {
    const rawSource = props.cell?.source?.join("\n");

    return marked.parse(rawSource);
});

const execute = (evt: any) => {
    cell.value.source = cellSource.value.split("\n");
    editing.value = false;
}

const enter = (evt: KeyboardEvent) => {
    editing.value = true;
    evt.preventDefault();
    evt.stopPropagation();
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
