<template>
    <Transition name="thinking-slide">
        <div v-if="isVisible" class="agent-thinking-indicator">
            <div class="thinking-content">
                <span class="thought-icon"><ThinkingIcon/></span>
                <span class="thinking-text">{{ thinkingText }}</span>
                <span class="thinking-animation"></span>
            </div>
            <Button 
                icon="pi pi-arrow-up" 
                text 
                size="small"
                @click="scrollToActiveQuery"
                v-tooltip="'Scroll to active query'"
                class="scroll-to-query-btn"
            />
        </div>
    </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import Button from 'primevue/button';
import ThinkingIcon from '../../assets/icon-components/BrainIcon.vue';

const props = defineProps<{
    activeQueryCells: Array<{id: string, source: string, status: string}>
}>();

const emit = defineEmits<{
    scrollToQuery: [queryId: string]
}>();

const isVisible = computed(() => {
    return props.activeQueryCells.some(cell => cell.status === 'busy');
});

const activeQuery = computed(() => {
    return props.activeQueryCells.find(cell => cell.status === 'busy');
});

const thinkingText = computed(() => {
    if (!activeQuery.value) return '';
    const truncatedQuery = activeQuery.value.source.length > 40 
        ? activeQuery.value.source.substring(0, 37) + '...' 
        : activeQuery.value.source;
    return `"${truncatedQuery}"`;
});

const scrollToActiveQuery = () => {
    if (activeQuery.value) {
        emit('scrollToQuery', activeQuery.value.id);
    }
};
</script>

<style lang="scss">
.agent-thinking-indicator {
    border: 1px solid var(--p-primary-300);
    padding: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    
    .thinking-content {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex: 1;
        min-width: 0; // allow text to shrink
        
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
            font-size: 0.85rem;
            color: var(--p-text-color);
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            min-width: 0;
        }
        
        .thinking-animation {
            font-size: 1rem;
            flex-shrink: 0;
            width: 3em; // prevents overflow
        }
    }
    
    .scroll-to-query-btn {
        flex-shrink: 0;
        opacity: 0.7;
        
        &:hover {
            opacity: 1;
        }
    }
}

.thinking-animation:after {
    overflow: hidden;
    display: inline-block;
    vertical-align: bottom;
    position: relative;
    animation: thinking-ellipsis 2000ms steps(36, end) infinite;
    content: "\2026\2026\2026"; /* 3 ellipsis */
    width: 3em;
}

@keyframes thinking-ellipsis {
    from {
        right: 3em; // start from off-screen, right
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

.thinking-slide-enter-active,
.thinking-slide-leave-active {
    transition: all 0.3s ease;
}

.thinking-slide-enter-from {
    transform: translateY(-100%);
    opacity: 0;
}

.thinking-slide-leave-to {
    transform: translateY(-100%);
    opacity: 0;
}

@media (max-width: 768px) {
    .agent-thinking-indicator {
        margin: 0 0.5rem 0.75rem 0.5rem;
        padding: 0.5rem;
        
        .thinking-content {
            gap: 0.25rem;
            
            .thinking-text {
                font-size: 0.8rem;
            }
            
            .thinking-animation {
                width: 2em;
            }
        }
    }
    
    .thinking-animation:after {
        content: "\2026\2026";
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
}
</style>
