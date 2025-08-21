<template>
    <div class="next-query-cell">
        <div class="query-cell-grid">
            <div class="query-content">
                <div class="query-prompt">
                    <div class="query-label">
                        <span class="pi pi-sparkles query-icon"></span>
                        <span>User Query:</span>
                    </div>
                    <div class="query-text">{{ cell.source }}</div>

                    <div class="query-controls">
                        <div v-if="showCollapseControl" class="collapse-control">
                            <Checkbox
                                v-model="autoCollapseCodeCells"
                                :binary="true"
                                :disabled="!isQueryActive"
                                inputId="auto-collapse-checkbox"
                            />
                            <label for="auto-collapse-checkbox" class="collapse-label">
                                Truncate code cells
                            </label>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="state-info">
                <div>
                    <Badge
                        class="execution-badge"
                        :class="{secondary: badgeSeverity === 'secondary'}"
                        :severity="badgeSeverity"
                        value=" "
                        v-tooltip.top="badgeTooltip">
                        <!-- <BrainIcon 
                            v-if="cell.metadata?.query_status === 'in-progress'" 
                            class="brain-icon" 
                        /> -->
                        <i :class="badgeIcon"></i>
                    </Badge>
                </div>
                <!-- <i
                    v-if="cell.status === 'busy' || cell.status === 'awaiting_input'"
                    class="pi pi-spin pi-spinner busy-icon"
                /> -->
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { inject, computed, onBeforeMount, getCurrentInstance, onBeforeUnmount, watchEffect, ref } from "vue";
import Badge from 'primevue/badge';
import type { BeakerSessionComponentType } from "../session/BeakerSession.vue";
import { useBaseQueryCell } from './BaseQueryCell';
// import BrainIcon from '../../assets/icon-components/BrainIcon.vue';
import Checkbox from 'primevue/checkbox';

const props = defineProps([
    'index',
    'cell',
]);

const {
  cell,
  events,
  execute,
  enter,
  exit,
  clear,
} = useBaseQueryCell(props);

const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
const instance = getCurrentInstance();

const autoCollapseCodeCells = ref(false);

const isQueryActive = computed(() => {
    const queryStatus = cell.value.metadata?.query_status;
    return queryStatus === 'in-progress' || queryStatus === 'pending';
});

const showCollapseControl = computed(() => {
    const queryStatus = cell.value.metadata?.query_status;
    return queryStatus === 'in-progress' || queryStatus === 'pending';
});

watchEffect(() => {
    if (cell.value.metadata) {
        cell.value.metadata.auto_collapse_code_cells = autoCollapseCodeCells.value;
    }
});

watchEffect(() => {
    const currentStatus = cell.value.status;
    const currentQueryStatus = cell?.value?.metadata?.query_status;
    const currentEvents = events.value;
    const currentLastExecution = cell.value.last_execution;
    
    if (currentStatus === 'busy' && currentQueryStatus === 'pending') {
        cell.value.metadata.query_status = 'in-progress'
        console.log('Transitioning to in-progress');
    } else if (currentStatus === 'failed') {
        cell.value.metadata.query_status = 'failed';
        console.log('Transitioning to failed');
    } else if (currentStatus === 'idle' && currentEvents.length >= 0 && currentQueryStatus === 'in-progress') {
        if (currentLastExecution?.status === 'abort') {
            cell.value.metadata.query_status = 'aborted';
            return;
        }
        
        const hasAbortEvent = currentEvents.some(event => event.type === 'abort');
        if (hasAbortEvent) {
            cell.value.metadata.query_status = 'aborted';
            return;
        }
        
        const hasResponseEvent = currentEvents.some(event => event.type === 'response');
        if (hasResponseEvent && currentEvents.length > 0) {
            cell.value.metadata.query_status = 'success';
        }
    }
});

const badgeSeverity = computed(() => {
    const queryStatus = cell.value.metadata?.query_status;
    
    switch (queryStatus) {
        case 'success':
            return 'success';
        case 'failed':
            return 'danger';
        case 'aborted':
            return 'warn';
        case 'in-progress':
        case 'pending':
        default:
            return 'secondary';
    }
});

const badgeIcon = computed(() => {
    const queryStatus = cell.value.metadata?.query_status;
    
    switch (queryStatus) {
        case 'success':
            return 'pi pi-check';
        case 'failed':
            return 'pi pi-times';
        case 'aborted':
            return 'pi pi-minus';
        case 'in-progress':
            return 'pi pi-spinner pi-spin busy-icon';
        case 'pending':
            return 'pi pi-clock';
        default:
            return null;
    }
});

const badgeTooltip = computed(() => {
    const queryStatus = cell.value.metadata?.query_status;
    
    switch (queryStatus) {
        case 'success':
            return 'Query completed successfully';
        case 'failed':
            return 'Query failed with error';
        case 'aborted':
            return 'Query was aborted';
        case 'in-progress':
            return 'Query is active';
        case 'pending':
            return 'Query is waiting to start';
        default:
            return 'Query status unknown';
    }
});

defineExpose({
    execute,
    enter,
    exit,
    clear,
    cell,
});

onBeforeMount(() => {
    if (beakerSession?.cellRegistry) {
      beakerSession.cellRegistry[cell.value.id] = instance.vnode;
    }

    if (!cell.value.metadata?.query_status) {
        if(cell.value.metadata) {
            cell.value.metadata.query_status = 'pending';
        }
    }
    
    if (cell.value.metadata?.auto_collapse_code_cells !== undefined) {
        autoCollapseCodeCells.value = cell.value.metadata.auto_collapse_code_cells;
    }
});

onBeforeUnmount(() => {
    delete beakerSession.cellRegistry[cell.value.id];
});

</script>

<style lang="scss">
.next-query-cell {
    background-color: var(--p-surface-a);
    border-radius: var(--p-surface-border-radius);
}

.query-cell-grid {
    display: grid;
    grid-template-areas:
        "content content content exec";
    grid-template-columns: 1fr 1fr 1fr auto;
}

.query-content {
    grid-area: content;
}

.state-info {
    grid-area: exec;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
}

.query-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    color: var(--p-text-color);
}

.query-icon {
    color: var(--p-primary-500);
    font-size: 1.1rem;
}

.query-text {
    background-color: var(--p-surface-0);
    border-radius: var(--p-surface-border-radius);
    white-space: pre-wrap;
    font-family: inherit;
    margin-top: 0.25rem;
}

.collapse-control {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0.5rem 0 0.25rem 0;
    background-color: var(--p-surface-0);
}

.collapse-label {
    font-size: 0.875rem;
    color: var(--p-text-color-secondary);
    cursor: pointer;
    user-select: none;
}

.execution-badge {
    font-family: 'Ubuntu Mono', 'Courier New', Courier, monospace;
    font-size: 1rem;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 2em;
    aspect-ratio: 1/1;
    border-radius: 15%;
    position: relative;
    
    &.secondary {
        background-color: var(--p-surface-e);
    }
    i {
        font-size: 0.9rem;
        position: absolute;
        color: inherit;
    }
}

.busy-icon {
    // color: var(--p-surface-a) !important;
    font-weight: bold;
    font-size: 1.3rem;
    // margin-right: 0.33rem;
}

.brain-icon {
    width: 1rem;
    height: 1rem;
    
    svg {
        width: 100%;
        height: 100%;
    }

    .brain-svg-path {
        fill: var(--p-badge-secondary-color);
    }
}
</style>
