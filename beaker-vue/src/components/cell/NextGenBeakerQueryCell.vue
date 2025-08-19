<template>
    <div class="nextgen-query-cell">
        <div class="query-cell-grid">
            <div class="query-content">
                <div class="query-prompt">
                    <div class="query-label">
                        <span class="pi pi-sparkles query-icon"></span>
                        <span>User Query:</span>
                    </div>
                    <div class="query-text">{{ cell.source }}</div>
                </div>
                
                <div class="input-request" v-if="cell.status === 'awaiting_input'">
                    <div class="input-request-wrapper">
                        <InputGroup>
                            <InputText
                                placeholder="Reply to the agent"
                                @keydown.enter.exact.prevent="respond"
                                @keydown.escape.prevent.stop="($event.target as HTMLElement).blur()"
                                autoFocus
                                v-model="response"
                            />
                            <Button
                                icon="pi pi-send"
                                @click="respond"
                            />
                        </InputGroup>
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
                        <BrainIcon 
                            v-if="cell.metadata?.query_status === 'in-progress'" 
                            class="brain-icon" 
                        />
                        <i v-else-if="badgeIcon" :class="badgeIcon"></i>
                    </Badge>
                </div>
                <i
                    v-if="cell.status === 'busy'"
                    class="pi pi-spin pi-spinner busy-icon"
                />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { inject, computed, onBeforeMount, getCurrentInstance, onBeforeUnmount, watchEffect } from "vue";
import Button from "primevue/button";
import Badge from 'primevue/badge';
import type { BeakerSessionComponentType } from "../session/BeakerSession.vue";
import InputGroup from 'primevue/inputgroup';
import InputText from 'primevue/inputtext';
import { useBaseQueryCell } from './BaseQueryCell';
import BrainIcon from '../../assets/icon-components/BrainIcon.vue';

const props = defineProps([
    'index',
    'cell',
]);

const {
  cell,
  response,
  events,
  execute,
  enter,
  exit,
  clear,
  respond
} = useBaseQueryCell(props);

const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
const instance = getCurrentInstance();

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
            return null;
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
            return 'Query is currently running';
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
});

onBeforeUnmount(() => {
    delete beakerSession.cellRegistry[cell.value.id];
});

</script>

<style lang="scss">
.nextgen-query-cell {
    background-color: var(--p-surface-a);
    border-radius: var(--p-surface-border-radius);
    margin-top: 0.75rem;
    margin-bottom: 0.5rem;
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

.query-prompt {
    margin-bottom: 0.75rem;
}

.query-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
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
    color: var(--p-blue-500);
    font-weight: bold;
    font-size: 1.3rem;
    margin-top: 1rem;
}

.input-request {
    padding: 0.5rem 0;
    display: flex;
    align-items: flex-start;
    width: 100%;
}

.input-request-wrapper {
    display: flex;
    width: 100%;
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
