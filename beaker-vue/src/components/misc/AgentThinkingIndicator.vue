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
    return `"${activeQuery.value.source}"`;
});

const scrollToActiveQuery = () => {
    if (activeQuery.value) {
        emit('scrollToQuery', activeQuery.value.id);
    }
};
</script>

<style lang="scss">

.beaker-dark {
    .agent-thinking-indicator {
        border: 1px solid var(--p-primary-200);
        background-color: var(--p-surface-c);
    }
}

.agent-thinking-indicator {
    // border: 1px solid var(--p-primary-400);
    padding: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;

    border-radius: var(--p-surface-border-radius);
    background-color: var(--p-surface-a);

    // box-shadow: var(--p-shadow-sm);
    // filter: drop-shadow(var(--p-shadow-sm));

    box-shadow: rgba(0, 0, 0, 0.24) 0px 3px 8px;

    margin: 0.5rem 0.5rem 0.5rem 0.5rem;
    
    .thinking-content {
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        flex: 1;
        min-width: 0;
        
        .thought-icon {
            display: inline-block;
            height: 1rem;
            color: var(--p-primary-500);
            flex-shrink: 0;
            margin-top: 0.1rem;
            
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
            min-width: 0;
            display: -webkit-box;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: 2;
            overflow: hidden;
            line-height: 1.3;
            max-height: calc(1.3em * 2);
        }
        
        .thinking-animation {
            font-size: 1rem;
            flex-shrink: 0;
            width: 2.5em;
            align-self: flex-end;
            margin-top: auto;
            margin-left: 1.75rem;
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
            align-items: flex-start;
            
            .thinking-text {
                font-size: 0.8rem;
            }
            
            .thinking-animation {
                width: 1.5em;
                align-self: flex-end;
            }
        }
    }
    
    .thinking-animation:after {
        content: "\2026\2026";
        width: 1.5em;
    }
    
    @keyframes thinking-ellipsis {
        from {
            right: 1.5em;
        }
        to {
            right: 0;
        }
    }
}

@media (max-width: 480px) {
    .agent-thinking-indicator {
        .thinking-content {
            .thinking-animation {
                width: 1.2em;
            }
        }
    }
    
    .thinking-animation:after {
        width: 1.2em;
    }
    
    @keyframes thinking-ellipsis {
        from {
            right: 1.2em;
        }
        to {
            right: 0;
        }
    }
}
</style>
