<template>
        <div class="code-cell">
            <div class="code-cell-grid">
                <div
                    class="code-data"
                    :class="{'dark-mode': theme.mode === 'dark'}"
                >
                    <CodeEditor
                        display-mode="dark"
                        :language="language"
                        v-model="cell.source"
                        ref="codeEditorRef"
                        placeholder="Your code..."
                        :disabled="isBusy"
                        @change="handleCodeChange"
                        @click="clicked"
                    />
                    <CodeCellOutput :outputs="cell.outputs" :busy="isBusy" v-show="!hideOutput" />
                </div>
                <div class="state-info">
                    <div class="execution-count-badge">
                        <Badge
                            :class="{secondary: badgeSeverity === 'secondary'}"
                            :severity="badgeSeverity"
                            :value="cell.execution_count || '&nbsp;'">
                        </Badge>
                    </div>
                    <i
                        v-if="isBusy"
                        class="pi pi-spin pi-spinner busy-icon"
                    />
                    <Button
                        v-if="hasRollback"
                        class="rollback-button"
                        :severity="badgeSeverity"
                        icon="pi pi-refresh"
                        size="small"
                        @click="rollback"
                    />
                </div>
            </div>
        </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, defineExpose, ref, shallowRef, computed, inject, getCurrentInstance, onBeforeMount, onBeforeUnmount } from "vue";
import CodeCellOutput from "./BeakerCodeCellOutput.vue";
import Badge from 'primevue/badge';
import Button from 'primevue/button';
import { findSelectableParent } from "@/util";
import { BeakerSession } from "beaker-kernel";
import CodeEditor from "@/components/misc/CodeEditor.vue";
import { BeakerSessionComponentType } from '@/components/session/BeakerSession.vue';
import { BeakerNotebookComponentType } from '@/components/notebook/BeakerNotebook.vue';

const props = defineProps([
    "cell",
    "hideOutput"
]);

const cell = ref(props.cell);
const { theme } = inject('theme');
const session = inject<BeakerSession>('session');
const codeEditorRef = ref<InstanceType<typeof CodeEditor>>();
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
const notebook = inject<BeakerNotebookComponentType>("notebook");
const instance = getCurrentInstance();

const emit = defineEmits([
    'blur',
])

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

const clicked = (evt) => {
    notebook.selectCell(cell.value, true);
    evt.stopPropagation();
};

function handleCodeChange() {
    cell.value.reset_execution_state();
}

const language = computed(() => (beakerSession.activeContext?.language?.slug || undefined));

const execute = (evt: any) => {
    const future = props.cell.execute(session);

}

const enter = () => {
    codeEditorRef.value?.focus();
}

const exit = () => {
    // Be sure to blur editor even if we don't also refocus below.
    codeEditorRef.value?.blur();
    let target: HTMLElement = (instance.vnode.el as HTMLElement);
    const selectableParent = findSelectableParent(target);
    selectableParent?.focus();
}

const clear = () => {
    cell.value.source = "";
    cell.value.outputs.splice(0, cell.value.outputs.length);
}

defineExpose({
    execute,
    enter,
    exit,
    clear,
});

onBeforeMount(() => {
    beakerSession.cellRegistry[cell.value.id] = instance.vnode;
});

onBeforeUnmount(() => {
    delete beakerSession.cellRegistry[cell.value.id];
});

</script>

<script lang="ts">
import { BeakerCodeCell } from "beaker-kernel";
export default {
    modelClass: BeakerCodeCell
};
</script>

<style lang="scss">
.code-cell {
    padding-left: 16px;
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
