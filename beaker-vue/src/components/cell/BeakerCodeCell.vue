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
                    <div>
                        <Badge
                            class="execution-count-badge"
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
                        icon="pi pi-undo"
                        size="small"
                        @click="rollback"
                    />
                </div>
            </div>
        </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, defineExpose, ref, shallowRef, computed, inject, getCurrentInstance, onBeforeMount, onBeforeUnmount, nextTick } from "vue";
import CodeCellOutput from "./BeakerCodeCellOutput.vue";
import Badge from 'primevue/badge';
import Button from 'primevue/button';
import { findSelectableParent } from "../../util";
import { BeakerSession } from "beaker-kernel/src";
import CodeEditor from "../misc/CodeEditor.vue";
import { type BeakerSessionComponentType } from '../session/BeakerSession.vue';
import { type BeakerNotebookComponentType } from '../notebook/BeakerNotebook.vue';
import { IBeakerTheme } from '../../plugins/theme';

const props = defineProps([
    "cell",
    "hideOutput"
]);

const cell = ref(props.cell);
const { theme } = inject<IBeakerTheme>('theme');
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
    const defaultValue = "secondary";
    const mappings = {
        [ExecuteStatus.Success]: 'success',
        [ExecuteStatus.Modified]: 'warning',
        [ExecuteStatus.Error]: 'danger',
        [ExecuteStatus.Pending]: defaultValue,
        [ExecuteStatus.None]: defaultValue,
    };
    return mappings[cell.value?.last_execution?.status] || defaultValue;
});

const clicked = (evt) => {
    if (notebook) {
        notebook.selectCell(cell.value);
    }
    evt.stopPropagation();
};

function handleCodeChange() {
    cell.value.reset_execution_state();
}

const language = computed(() => (beakerSession.activeContext?.language?.slug || undefined));

const execute = (evt: any) => {
    const future = props.cell.execute(session);
    exit();
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
    cell,
});

onBeforeMount(() => {
    beakerSession.cellRegistry[cell.value.id] = instance.vnode;
});

onBeforeUnmount(() => {
    delete beakerSession.cellRegistry[cell.value.id];
});

</script>

<script lang="ts">
import { BeakerCodeCell } from "beaker-kernel/src";
export default {
    modelClass: BeakerCodeCell,
    icon: "pi pi-code",
};
</script>

<style lang="scss">
.code-cell {
    // padding-left: 16px;
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
    margin-left: 0.5rem;
    font-family: "'Ubuntu Mono', 'Courier New', Courier, monospace";
    font-size: 1.1rem;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 2em;
    aspect-ratio: 1/1;
    border-radius: 15%;
    &.secondary {
        background-color: var(--surface-300);
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
