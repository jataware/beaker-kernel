<template>
    <div class="markdown-cell"
        @dblclick="enter()"
    >
        <div v-if="!isEditing" v-html="renderedMarkdown"></div>
        <div v-else>
            <div class="markdown-edit-cell-grid">
                <div
                    class="markdown-edit-data"
                    :class="{'dark-mode': theme.mode === 'dark'}"
                    :ref="editorRef"
                >
                    <CodeEditor
                        v-model="editorContents"
                        placeholder="Your markdown..."
                        ref="codeEditorRef"
                        :autofocus="false"
                        language="markdown"
                        display-mode="dark"
                        @click="clicked"
                    />
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps, ref, inject, computed, nextTick, onBeforeMount, defineExpose, getCurrentInstance, onBeforeUnmount} from "vue";
import { marked } from 'marked';
import { findSelectableParent } from '../../util';
import { type BeakerSessionComponentType } from '../session/BeakerSession.vue';
import { type BeakerNotebookComponentType } from '../notebook/BeakerNotebook.vue';
import CodeEditor from '../misc/CodeEditor.vue';
import { IBeakerTheme } from '../../plugins/theme';

const props = defineProps([
    "cell"
]);

const instance = getCurrentInstance();
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
const cell = ref(props.cell);
const { theme } = inject<IBeakerTheme>('theme');
const isEditing = ref(false);
const editorRef = ref(null);
const codeEditorRef = ref(null);
const notebook = inject<BeakerNotebookComponentType>("notebook");
const editorContents = ref<string>(cell.value.source);

const renderedMarkdown = computed(() => {
    return marked.parse(props.cell?.source || "");
});

const clicked = (evt) => {
    notebook.selectCell(cell.value);
    evt.stopPropagation();
};

const execute = () => {
    isEditing.value = false;
    cell.value.source = editorContents.value;
}

const enter = () => {
    if (!isEditing.value) {
        isEditing.value = true;
    }

    nextTick(() => {
        codeEditorRef.value?.focus();
    });
}

const exit = () => {
    codeEditorRef.value?.blur();
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
    model: cell,
});

onBeforeMount(() => {
    marked.setOptions({
    //    gfm: true,
    //    sanitize: false,
    //    langPrefix: `language-`,
     });
    beakerSession.cellRegistry[cell.value.id] = instance.vnode;
})

onBeforeUnmount(() => {
    delete beakerSession.cellRegistry[cell.value.id];
});

</script>

<script lang="ts">
import { BeakerMarkdownCell } from "beaker-kernel/src";
export default {
    modelClass: BeakerMarkdownCell,
    icon: "pi pi-pencil",
};
</script>

<style lang="scss">

.markdown-cell {
    padding-right: 2rem;
    // padding-left: 1rem;
    // min-height: 80%;
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
