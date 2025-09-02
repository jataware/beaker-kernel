<template>
    <div 
        class="next-query-cell" 
        ref="queryCellRef"
        :class="{ 'sticky-query': isSticky }"
        @click="handleCellClick"
        @wheel="handleWheelEvent"
    >
        <div v-if="forceMock && isSelected" class="mock-controls">
            <button @click="toggleMockSticky" class="mock-button">
                {{ mockStickyForce ? 'Disable' : 'Enable' }} Sticky Test
            </button>
            <span class="status-debug">
                Mock: {{ mockStickyForce ? 'ON' : 'OFF' }} | 
                Status: {{ cell.metadata?.query_status || 'undefined' }}
            </span>
        </div>
        
        <div class="query-cell-grid">
            <div class="query-content">
                <div class="query-prompt">
                    <div class="query-label">
                        <span class="pi pi-user query-icon"></span>
                        <span class="query-label-user">User</span>
                    </div>
                    <div class="query-text">{{ cell.source }}</div>
                    
                    <div v-if="shouldShowThought && lastThoughtText" class="last-thought">
                        <div class="thought-label">
                            <span class="pi pi-robot thought-icon"></span>
                            <span class="thought-label-text">Assistant</span>
                        </div>
                        <div class="thought-content">{{ lastThoughtText }}</div>
                    </div>
                    
                    <div v-if="!isSticky && isQueryActive" class="thinking-indicator">
                        <span class="thought-icon">
                            <ThinkingIcon/>
                        </span>
                        <span class="thinking-text">Assistant Running</span>
                        <span class="thinking-animation"></span>
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
                        <i :class="badgeIcon"></i>
                    </Badge>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { inject, computed, onBeforeMount, getCurrentInstance, onBeforeUnmount, watchEffect, ref, nextTick } from "vue";
import Badge from 'primevue/badge';
import ThinkingIcon from '../../assets/icon-components/BrainIcon.vue';
import type { BeakerSessionComponentType } from "../session/BeakerSession.vue";
import type { BeakerNotebookComponentType } from "../notebook/BeakerNotebook.vue";
import { useBaseQueryCell } from './BaseQueryCell';
// import Checkbox from 'primevue/checkbox';

const props = defineProps([
    'index',
    'cell',
]);

const {
  cell,
  events,
  execute,
//   enter,
  exit,
  clear,
} = useBaseQueryCell(props);

const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
const notebook = inject<BeakerNotebookComponentType>("notebook");
const instance = getCurrentInstance();

const autoCollapseCodeCells = ref(false);
const queryCellRef = ref<HTMLElement | null>(null);
const isSticky = ref(false);

const mockStickyForce = ref(false);

const forceMock = computed(() => {
    return false;
    // return true;
});

const isSelected = computed(() => {
    return cell.value.id === notebook?.selectedCellId;
});

const lastThoughtText = computed(() => {
    const thoughtEvents = events.value.filter(event => event.type === 'thought');
    if (thoughtEvents.length === 0) return null;
    
    const lastThought = thoughtEvents[thoughtEvents.length - 1];
    
    if (typeof lastThought.content === 'string') {
        return lastThought.content;
    } else if (typeof lastThought.content === 'object' && lastThought.content?.thought) {
        return lastThought.content.thought;
    } else if (typeof lastThought.content === 'object') {
        const content = lastThought.content;
        return content.thought || content.text || content.message || JSON.stringify(content);
    }
    
    return null;
});

const shouldShowThought = computed(() => {
    return isSticky.value && isQueryActive.value;
});

const toggleMockSticky = () => {
    mockStickyForce.value = !mockStickyForce.value;
    console.log('Mock sticky force:', mockStickyForce.value);
};

const isQueryActive = computed(() => {
    if (mockStickyForce.value) return true; // Force active for testing
    
    const queryStatus = cell.value.metadata?.query_status;
    return queryStatus === 'in-progress' || queryStatus === 'pending';
});

// const showCollapseControl = computed(() => {
//     const queryStatus = cell.value.metadata?.query_status;
//     return queryStatus === 'in-progress' || queryStatus === 'pending';
// });

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
    if (mockStickyForce.value) return 'info';
    
    const queryStatus = cell.value.metadata?.query_status;
    
    switch (queryStatus) {
        case 'success':
            return 'success';
        case 'failed':
            return 'danger';
        case 'aborted':
            return 'warn';
        case 'in-progress':
            return 'info';
        case 'pending':
        default:
            return 'secondary';
    }
});

const badgeIcon = computed(() => {
    if (mockStickyForce.value) return 'pi pi-spinner pi-spin busy-icon';
    
    const queryStatus = cell.value.metadata?.query_status;
    
    switch (queryStatus) {
        case 'success':
            return 'pi pi-check bolded';
        case 'failed':
            return 'pi pi-times';
        case 'aborted':
            return 'pi pi-minus';
        case 'in-progress':
            return 'pi pi-spin pi-spinner busy-icon';
        case 'pending':
            return 'pi pi-clock';
        default:
            return null;
    }
});

const badgeTooltip = computed(() => {
    if (mockStickyForce.value) return 'Mock sticky mode active';
    
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

const setupStickyBehavior = () => {
    const cellContainer = queryCellRef.value?.closest('.cell-container') as HTMLElement;
    if (!cellContainer) {
        return;
    }

    let ticking = false;

    const updateStickyPosition = () => {
        if (!queryCellRef.value || !isSticky.value) return;
        
        const containerRect = cellContainer.getBoundingClientRect();
        queryCellRef.value.style.setProperty('--sticky-top', `${containerRect.top}px`);
        queryCellRef.value.style.setProperty('--sticky-left', `${containerRect.left}px`);
        queryCellRef.value.style.setProperty('--sticky-right', `${window.innerWidth - containerRect.right}px`);
    };

    const handleScroll = () => {
        if (!ticking) {
            requestAnimationFrame(() => {
                if (!queryCellRef.value || !isQueryActive.value) {
                    ticking = false;
                    return;
                }

                const beakerCell = queryCellRef.value.closest('.beaker-cell') as HTMLElement;
                if (!beakerCell) {
                    ticking = false;
                    return;
                }

                const cellRect = beakerCell.getBoundingClientRect();
                const containerRect = cellContainer.getBoundingClientRect();
                
                if (cellRect.top < (containerRect.top - 30) && !isSticky.value) {
                    isSticky.value = true;
                    updateStickyPosition();
                    
                } else if (cellRect.top >= containerRect.top && isSticky.value) {
                    isSticky.value = false;
                    
                    queryCellRef.value.style.removeProperty('--sticky-top');
                    queryCellRef.value.style.removeProperty('--sticky-left');
                    queryCellRef.value.style.removeProperty('--sticky-right');
                } else if (isSticky.value) {
                    updateStickyPosition();
                }
                
                ticking = false;
            });
            ticking = true;
        }
    };

    let resizeObserver: ResizeObserver | null = null;
    if (window.ResizeObserver) {
        resizeObserver = new ResizeObserver(() => {
            if (isSticky.value) {
                updateStickyPosition();
            }
        });
        resizeObserver.observe(cellContainer);
    }

    cellContainer.addEventListener('scroll', handleScroll, { passive: true });
    
    return () => {
        cellContainer.removeEventListener('scroll', handleScroll);
        if (resizeObserver) {
            resizeObserver.disconnect();
        }
    };
};

const handleQueryCompletion = async () => {
    if (!isSticky.value) return;
    
    await nextTick();
    
    if (queryCellRef.value) {
        queryCellRef.value.style.removeProperty('--sticky-top');
        queryCellRef.value.style.removeProperty('--sticky-left');
        queryCellRef.value.style.removeProperty('--sticky-right');
    }
    
    isSticky.value = false;
    
    // This would scroll back to the query cell when it's completed
    // but we may not want that. We may want to scroll to the assistant response cell,
    // or not at all. Leaving this in commented, as an option, for now.
    // if (queryCellRef.value) {
    //     const beakerCell = queryCellRef.value.closest('.beaker-cell') as HTMLElement;
    //     if (beakerCell) {
    //         beakerCell.scrollIntoView({ 
    //             behavior: 'smooth', 
    //             block: 'start' 
    //         });
    //     }
    // }
};

watchEffect(() => {
    if (mockStickyForce.value) return;
    
    const queryStatus = cell.value.metadata?.query_status;
    if (queryStatus === 'success' || queryStatus === 'failed' || queryStatus === 'aborted') {
        if (isSticky.value) {
            handleQueryCompletion();
        }
    }
});

const handleCellClick = (event: MouseEvent) => {
    if (isSticky.value) {
        event.preventDefault();
        event.stopPropagation();
    }
};

const handleWheelEvent = (event: WheelEvent) => {
    if (isSticky.value) {
        event.preventDefault();
        event.stopPropagation();
        
        const cellContainer = queryCellRef.value?.closest('.cell-container') as HTMLElement;
        if (cellContainer) {
            cellContainer.scrollTop += event.deltaY;
            cellContainer.scrollLeft += event.deltaX;
        }
    }
};

let cleanupSticky: (() => void) | undefined;

defineExpose({
    execute,
    enter: () => {},
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
    
    nextTick(() => {
        cleanupSticky = setupStickyBehavior();
    });
});

onBeforeUnmount(() => {
    delete beakerSession.cellRegistry[cell.value.id];
    if (cleanupSticky) {
        cleanupSticky();
    }
    
    if (queryCellRef.value) {
        queryCellRef.value.style.removeProperty('--sticky-top');
        queryCellRef.value.style.removeProperty('--sticky-left');
        queryCellRef.value.style.removeProperty('--sticky-right');
    }
});

</script>

<style lang="scss">
.next-query-cell {
    background-color: var(--p-surface-a);
    border-radius: var(--p-surface-border-radius);
    position: relative;
    
    &.sticky-query {
        position: fixed !important;
        top: var(--sticky-top, 0) !important;
        left: var(--sticky-left, 0) !important;
        right: var(--sticky-right, 0) !important;
        z-index: 500 !important;
        // box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15) !important;
        box-shadow: 0rem 0.25rem 1rem rgba(0, 0, 0, 0.6) !important;

       border: 1px solid var(--p-purple-500) !important;

        border-radius: 6px !important;
        background-color: var(--p-surface-a) !important;

        padding: 8px 12px !important;
        margin: 0.5rem !important;
        
        pointer-events: auto !important;
        
        .query-cell-grid {
            margin: 0 !important;
        }
        
        .query-content {
            margin: 0.1rem 0.25rem 0.33rem 0rem !important;
        }
        
        animation: stickySlideDown 0.2s ease-out;
    }
}

@keyframes stickySlideDown {
    from {
        transform: translateY(-10px);
        opacity: 0.9;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

.mock-controls {
    position: absolute;
    top: -40px;
    right: 0;
    z-index: 10;
    display: flex;
    align-items: center;
    gap: 8px;
    
    .mock-button {
        background: var(--p-orange-500);
        color: white;
        border: none;
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 12px;
        cursor: pointer;
        opacity: 0.8;
        
        &:hover {
            opacity: 1;
            background: var(--p-orange-600);
        }
    }
    
    .status-debug {
        font-size: 10px;
        color: var(--p-text-color-secondary);
        background: var(--p-surface-0);
        padding: 2px 6px;
        border-radius: 3px;
        white-space: nowrap;
    }
}

.last-thought {
    margin-top: 0.5rem;
    padding: 0.5rem;
    background-color: var(--p-surface-b);
    border-radius: var(--p-surface-border-radius);
    
    .thought-label {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--p-text-color-secondary);
        margin-bottom: 0.25rem;
        
        .thought-icon {
            color: var(--p-primary-500);
            font-size: 0.875rem;
        }
    }
    
    .thought-content {
        font-size: 0.875rem;
        color: var(--p-text-color);
        line-height: 1.4;
        white-space: pre-wrap;
    }
}

.query-cell-grid {
    display: grid;
    grid-template-areas:
        "content content content exec";
    grid-template-columns: 1fr 1fr 1fr auto;
}

.query-content {
    grid-area: content;
    margin: 0.1rem 0.25rem 0.33rem 0rem;
}

.state-info {
    grid-area: exec;
    display: flex;
    flex-direction: column;
}

.query-label {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-weight: 600;
    min-height: 1.8rem;

    .query-label-user {
        color: var(--p-green-600);
    }
}

.query-icon {
    color: var(--p-green-600);
    // font-size: 1.1rem;
}

.query-text {
    border-radius: var(--p-surface-border-radius);
    white-space: pre-wrap;
    font-family: inherit;
    margin-top: 0.33rem;
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
        font-size: 1rem;
        position: absolute;
        color: inherit;
    }
}

.busy-icon {
    font-weight: bold;
    margin: 0;
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

.bolded {
    font-weight: bold;
}

.thinking-indicator {
    margin-top: 0.5rem;
    padding: 0.5rem;
    background-color: var(--p-surface-b);
    border-radius: var(--p-surface-border-radius);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    
    .thought-icon {
        display: inline-block;
        height: 1rem;
        color: var(--p-primary-500);
        flex-shrink: 0;
        
        svg {
            fill: currentColor;
            stroke: currentColor;
            width: 1rem;
            animation: thinking-pulse 2s ease-in-out infinite;
        }
    }
    
    .thinking-text {
        font-size: 0.875rem;
        color: var(--p-text-color);
        font-weight: 500;
    }
    
    .thinking-animation {
        font-size: 1rem;
        flex-shrink: 0;
        width: 2.5em;
        margin-left: auto;
    }
}

.thinking-animation:after {
    overflow: hidden;
    display: inline-block;
    vertical-align: bottom;
    position: relative;
    animation: thinking-ellipsis 2000ms steps(36, end) infinite;
    content: "\2026\2026\2026";
    width: 2.5em;
}

@keyframes thinking-ellipsis {
    from {
        right: 2.5em;
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
