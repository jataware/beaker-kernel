<template>
    <div class="code-cell">
        <div class="code-cell-grid">
            <div
                class="code-data"
                :class="{'dark-mode': theme === 'dark'}"
            >
                <Codemirror
                    v-model="cell.source"
                    ref="codemirrorRef"
                    placeholder="Your code..."
                    :extensions="codeExtensions"
                    :disabled="isBusy"
                    :autofocus="true"
                    @change="handleCodeChange"
                    @ready="handleReady"
                />
                <CodeCellOutput :outputs="cell.outputs" :busy="isBusy" />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, defineExpose, ref, shallowRef, computed, inject } from "vue";
import CodeCellOutput from "./BeakerCodecellOutput.vue";
import { Codemirror } from "vue-codemirror";
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';
import Badge from 'primevue/badge';

const props = defineProps([
    "cell",
    "cell-state",
]);

const emit = defineEmits([
    "cell-state-changed",
]);

const cell = ref(props.cell);
const isBusy = ref(false);
const editorView = shallowRef();
const theme = inject('theme');
const session = inject('session');
const activeContext = inject('active_context');
const codemirrorRef = ref<typeof Codemirror|null>(null);

const handleReady = (payload) => {
    // TODO unused, but very useful for future operations.
    // See vue codemirror api/npm docs.
    editorView.value = payload.view;
};

function handleCodeChange() {
    // emit("cell-state-changed", ExecuteStatus.Modified);
    console.log("current state:", props.cellState);
    if (props.cellState !== "modified" && props.cellState !== "pending") {
        emit("cell-state-changed", "modified");
    }
    // if (executeState.value !== ExecuteStatus.Pending) {
    //     executeState.value = ExecuteStatus.Modified;
    // }

    // TODO See codemirror view API for future keyboard navigation
    // eg to know if we're at the top or bottom
    // of editor and user presser up/down arrows keys to navigate
    // to another cell
    // console.log(editorView.value.inputState);

}

const codeExtensions = computed(() => {
    const ext = [];

    const subkernel = activeContext.value?.language?.subkernel || '';
    const isPython = subkernel.includes('python');
    if (isPython) {
        ext.push(python());
    }
    if (theme.value === 'dark') {
        ext.push(oneDark);
    }
    return ext;

});

const execute = (evt: any) => {
    isBusy.value = true;

    const handleDone = async (message: any) => {

        if (message?.content?.status === 'ok') {
            // executeState.value = ExecuteStatus.Success;
            emit("cell-state-changed", "success");
        } else {
            // executeState.value = ExecuteStatus.Error;
            emit("cell-state-changed", "error");
        }


        // Timeout added to busy indicators from jumping in/out too quickly
        setTimeout(() => {
            isBusy.value = false;
        }, 500);

    };

    const future = props.cell.execute(session);
    future.done.then(handleDone);
    // executeState.value = ExecuteStatus.Pending;
    emit("cell-state-changed", "pending");
}

const enter = () => {
    if(codemirrorRef.value?.focus) {
        codemirrorRef.value?.focus();
    }
}

defineExpose({
    execute,
    enter,
});


</script>


<style lang="scss">
.code-cell-grid {
    display: grid;

    grid-template-areas:
        "code code code exec";

    grid-template-columns: 1fr 1fr 1fr auto;
}

.code-data {
    grid-area: code;
    background-color: var(--surface-a);

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


</style>
