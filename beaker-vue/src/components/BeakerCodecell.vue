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
                <CodeCellOutput :outputs="cell.outputs" :busy="isBusy" :isVisible="true"/>
            </div>
            <div class="state-info">
                <div class="execution-count-badge">
                    <!-- <Badge
                        v-show="isVisible"
                        outlined
                        icon="pi pi-arrow-down-left-and-arrow-up-right-to-center"
                        size="small"
                        @click="toggleVisible"
                    /> -->
                </div>
                <i
                    v-if="isBusy"
                    class="pi pi-spin pi-spinner busy-icon"
                />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps, nextTick, defineExpose, ref, shallowRef, computed, inject } from "vue";
import CodeCellOutput from "./BeakerCodecellOutput.vue";
import { Codemirror } from "vue-codemirror";
import { EditorView } from "codemirror";
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';
import Badge from 'primevue/badge';
import Button from 'primevue/button';


const props = defineProps([
    "cell",
]);

const cell = ref(props.cell);
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

enum ExecuteStatus {
  Success = 'ok',
  Modified = 'modified',
  Error = 'error',
  Pending = 'pending',
  None = 'none'
}

const hasRollback = computed(() => {
    return typeof(cell.value?.last_execution?.checkpoint_index) !== "undefined";
});

const rollback = () => cell.value.rollback(session);

const isBusy = computed(() => {
    return cell.value?.busy;
});

const badgeSeverity = computed(() => {
    const mappings = {
        [ExecuteStatus.Success]: 'success',
        [ExecuteStatus.Modified]: 'warning',
        [ExecuteStatus.Error]: 'danger',
        [ExecuteStatus.Pending]: 'secondary',
        [ExecuteStatus.None]: "secondary",
    };
    return mappings[cell.value?.last_execution?.status];
});


function handleCodeChange() {
    cell.value.reset_execution_state();
    // TODO See codemirror view API for future keyboard navigation
    // eg to know if we're at the top or bottom
    // of editor and user presser up/down arrows keys to navigate
    // to another cell
    // console.log(editorView.value.inputState);
}

const codeExtensions = computed(() => {
    const ext = [EditorView.lineWrapping];

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
    const future = props.cell.execute(session);
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
.code-cell {
    padding-left: 0.2rem;
}

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


.state-info {
    grid-area: exec;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.execution-count-badge {
    font-family: monospace;
    min-width: 3rem;
    display: flex;
    justify-content: center;

    .p-badge {
        border-radius: 15%;
        &.secondary {
            background-color: var(--surface-d);
        }
    }
}

.rollback-button {
    margin-top: 1rem;
    margin-left: auto;
    margin-right: auto;
    max-width: 45%;
}

.busy-icon {
    color: var(--blue-500);
    font-weight: bold;
    font-size: 1.3rem;
    margin-top: 1rem;
}

</style>
