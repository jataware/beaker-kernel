<template>
    <BeakerCell :cell="props.cell">
    <div class="raw-cell">
        <div class="raw-cell-header">
            <span class="raw-cell-title">Raw cell</span>
            <span v-if="props.cell.cell_type !== 'raw'"> - (Unrenderable cell type '{{ props.cell.cell_type }}')</span>
        </div>
        <Codemirror
            v-model="cell.source"
            ref="codemirrorRef"
            placeholder="Raw cell content..."
            :extensions="rawExtensions"
            :autofocus="true"
            @ready="handleReady"
        />
    </div>
    </BeakerCell>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, defineExpose, ref, shallowRef, computed, inject } from "vue";
import CodeCellOutput from "./BeakerCodecellOutput.vue";
import { Codemirror } from "vue-codemirror";
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';
import Badge from 'primevue/badge';
import BeakerCell from "./BeakerCell.vue";

const props = defineProps([
    "cell",
]);

const cell = ref(props.cell);
const isBusy = ref(false);
const editorView = shallowRef();
const theme = inject('theme');
const session = inject('session');
const activeContext = inject('activeContext');
const codemirrorRef = ref<typeof Codemirror|null>(null);

const handleReady = (payload) => {
    // TODO unused, but very useful for future operations.
    // See vue codemirror api/npm docs.
    editorView.value = payload.view;
};

enum ExecuteStatus {
  Success = 'success',
  Modified = 'modified',
  Error = 'error',
  Pending = 'pending',
}

const executeState = ref<ExecuteStatus>(ExecuteStatus.Pending);

const rawExtensions = computed(() => {
    const ext = [];
    // if (theme.value === 'dark') {
    //     ext.push(oneDark);
    // }
    return ext;

});

const execute = (evt: any) => {
    // No op
}

const enter = () => {
    if(codemirrorRef.value?.focus) {
        codemirrorRef.value?.focus();
    }
}

const exit = () => {
    window.blur();
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
