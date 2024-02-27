<template>

    <div class="code-cell">
        <div class="code-cell-grid">
            <div class="code-data">
                <Codemirror
                    v-model="cell.source"
                    placeholder="Your code..."
                    :extensions="codeExtensions"
                    :disabled="isBusy"
                    :autofocus="true"
                    @change="handleCodeChange"
                    @keydown.ctrl.enter.self.stop.prevent="execute"
                    @keydown.alt.enter="console.log('alt-enter')"
                    @keydown.shift.enter.prevent="execute"
                    @keydown.meta.enter="console.log('meta-enter')"
                />
                <CodeCellOutput :outputs="cell.outputs" :busy="isBusy" />
            </div>
            <div class="execution-count-badge">
                <Badge 
                    v-if="executeState !== ExecuteStatus.Pending"
                    :severity="badgeSeverity"
                    :value="cell.execution_count">
                </Badge>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps, ref, computed, inject } from "vue";
import CodeCellOutput from "./BeakerCodecellOutput.vue";
import { Codemirror } from "vue-codemirror";
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';
import Badge from 'primevue/badge';

const props = defineProps([
    "cell",
    "session",
    "contextData",
]);

const cell = ref(props.cell);
const isBusy = ref(false);
const theme = inject('theme');

enum ExecuteStatus {
  Success = 'success',
  Modified = 'modified',
  Error = 'error',
  Pending = 'pending',
}

const executeState = ref<ExecuteStatus>(ExecuteStatus.Pending);

const badgeSeverity = computed(() => {
    const mappings = {
        [ExecuteStatus.Success]: 'success',
        [ExecuteStatus.Modified]: 'warning',
        [ExecuteStatus.Error]: 'danger',
        [ExecuteStatus.Pending]: 'secondary',
    };
    return mappings[executeState.value];
});

function handleCodeChange() {
    if (executeState.value !== ExecuteStatus.Pending) {
        executeState.value = ExecuteStatus.Modified;
    }
}

const codeExtensions = computed(() => {
    const ext = [];

    const subkernel = props?.contextData?.language?.subkernel || '';
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
            executeState.value = ExecuteStatus.Success;
        } else {
            executeState.value = ExecuteStatus.Error;
        }
        
        // Timeout added to busy indicators from jumping in/out too quickly
        setTimeout(() => {
            isBusy.value = false;
        }, 1000);

    };

    evt.preventDefault();
    evt.stopPropagation();
    const future = props.cell.execute(props.session);
    future.done.then(handleDone);
}

</script>


<style lang="scss">
.code-cell {
    padding-left: 1rem;
}

.code-cell-grid {
    display: grid;

    grid-template-areas:
        "code code code exec";

    grid-template-columns: 1fr 1fr 1fr auto;
}

.code-data {
    grid-area: code;
}

.execution-count-badge {
    grid-area: exec;
    font-family: monospace;
    min-width: 3rem;
    display: flex;
    justify-content: center;

    &.pending {
        visibility: hidden;
    }
}

</style>
