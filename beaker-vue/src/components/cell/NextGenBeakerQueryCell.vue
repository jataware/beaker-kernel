<template>
    <div class="nextgen-query-cell">
        <div class="query-prompt">
            <div class="query-label">
                <span class="pi pi-sparkles query-icon"></span>
                <span>User Query:</span>
            </div>
            <div class="query-text">{{ cell.source }}</div>
        </div>
        
        <div class="query-status">
            <div class="thinking-indicator" v-if="cell.status === 'busy'">
                <span class="thought-icon"><ThinkingIcon/></span>
                <span class="thinking-text">Agent is thinking</span>
                <span class="thinking-animation"></span>
            </div>
            <div class="completed-indicator" v-else-if="isCompleted">
                <span class="pi pi-check-circle"></span>
                <span>Completed</span>
            </div>
            <div class="input-request" v-else-if="cell.status === 'awaiting_input'">
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
    </div>
</template>

<script setup lang="ts">
import { inject, computed, onBeforeMount, getCurrentInstance, onBeforeUnmount } from "vue";
import Button from "primevue/button";
import type { BeakerSessionComponentType } from "../session/BeakerSession.vue";
import ThinkingIcon from "../../assets/icon-components/BrainIcon.vue";
import InputGroup from 'primevue/inputgroup';
import InputText from 'primevue/inputtext';
import { useBaseQueryCell } from './BaseQueryCell';

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

const isCompleted = computed(() => {
    return cell.value.status === 'idle' && events.value.length > 0;
});

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
import { BeakerQueryCell } from "beaker-kernel";
export default {
    modelClass: BeakerQueryCell,
    icon: "pi pi-sparkles",
};
</script>

<style lang="scss">
.nextgen-query-cell {
    background-color: var(--p-surface-a);
    border-radius: var(--p-surface-border-radius);
    padding: 1rem;
    margin-bottom: 0.5rem;
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
    padding: 0.75rem;
    white-space: pre-wrap;
    font-family: inherit;
}

.query-status {
    display: flex;
    align-items: center;
}

.thinking-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background-color: var(--p-primary-50);
    border-radius: var(--p-surface-border-radius);
    color: var(--p-primary-700);
    
    .thought-icon {
        display: inline-block;
        height: 1rem;
        color: var(--p-primary-500);
        
        svg {
            fill: currentColor;
            stroke: currentColor;
            width: 1rem;
            animation: thinking-pulse 2s ease-in-out infinite;
        }
    }
    
    .thinking-text {
        font-weight: 500;
        font-size: 0.9rem;
    }
    
    .thinking-animation {
        font-size: 1rem;
        min-width: 2em;
    }
}

.completed-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background-color: var(--p-green-50);
    border-radius: var(--p-surface-border-radius);
    color: var(--p-green-700);
    
    .pi-check-circle {
        color: var(--p-green-500);
    }
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

.thinking-animation:after {
    overflow: hidden;
    display: inline-block;
    vertical-align: bottom;
    position: relative;
    animation: thinking-ellipsis 2000ms steps(24, end) infinite;
    content: "\2026\2026\2026";
    width: 2em;
}

@keyframes thinking-ellipsis {
    from {
        right: 2em;
    }
    to {
        right: 0;
    }
}

@keyframes thinking-pulse {
    0%, 100% {
        opacity: 1;
        transform: scale(1);
    }
    50% {
        opacity: 0.7;
        transform: scale(1.1);
    }
}
</style>
