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
                        value="1">
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
import { inject, computed, onBeforeMount, getCurrentInstance, onBeforeUnmount } from "vue";
import Button from "primevue/button";
import Badge from 'primevue/badge';
import type { BeakerSessionComponentType } from "../session/BeakerSession.vue";
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

const badgeSeverity = computed(() => {
    if (isCompleted.value) {
        return 'success';
    }
    return 'secondary';
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
    &.secondary {
        background-color: var(--p-surface-e);
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
</style>
