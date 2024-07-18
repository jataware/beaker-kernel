<template>
    <div class="raw-cell">
        <div class="raw-cell-header">
            <span class="raw-cell-title">Raw cell</span>
            <span v-if="props.cell.cell_type !== 'raw'"> - (Unrenderable cell type '{{ props.cell.cell_type }}')</span>
        </div>
        <Codemirror
            v-model="cell.source"
            ref="codeMirrorRef"
            placeholder="Raw cell content..."
            :extensions="rawExtensions"
            :autofocus="false"
            @ready="handleReady"
        />
    </div>
</template>

<script setup lang="ts">
import { defineProps, defineExpose, ref, shallowRef, computed, getCurrentInstance } from "vue";
import { Codemirror } from "vue-codemirror";
import { findSelectableParent } from "@/util";

const props = defineProps([
    "cell",
]);

const instance = getCurrentInstance();
const cell = ref(props.cell);
const codeMirrorRef = ref<typeof Codemirror|null>(null);
const codeMirrorEditorView = shallowRef();
const codeMirrorEditorState = shallowRef();

const handleReady = ({view, state}) => {
    // See vue codemirror api/npm docs: https://codemirror.net/docs/ref/
    codeMirrorEditorView.value = view;
    codeMirrorEditorState.value = state;
};

enum ExecuteStatus {
  Success = 'success',
  Modified = 'modified',
  Error = 'error',
  Pending = 'pending',
}

const rawExtensions = computed(() => {
    const ext = [];
    // if (theme.value === 'dark') {
    //     ext.push(oneDark);
    // }
    return ext;

});


const execute = (evt: any) => {
    // Nothing to do but exit
    exit();
}

const enter = () => {
    if(codeMirrorEditorView.value?.focus) {
        codeMirrorEditorView.value?.focus();
    }
}

const exit = () => {
    // Be sure to blur editor even if we don't also refocus below.
    if(codeMirrorEditorView.value?.blur) {
        codeMirrorEditorView.value?.blur();
    }
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


</script>


<style lang="scss">
.raw-cell {
    padding-left: 0.2rem;

    .cm-editor {
        border: 1px solid var(--surface-d);
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

.raw-cell-header {
    margin-bottom: 0.5rem;
}

.raw-cell-title {
    font-weight: bold;
    font-size: large;
}
</style>
