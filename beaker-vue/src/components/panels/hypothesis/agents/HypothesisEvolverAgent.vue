<template>
    <div v-if="output.parsed" class="evolver-agent">
        <!-- Compact view: evolution and toggle on one line -->
        <div class="compact-row">
            <div v-if="output.parsed.original_hypothesis_text" class="evolution-compact">
                <span class="compact-text from">{{ truncate(output.parsed.original_hypothesis_text, 40) }}</span>
                <i class="pi pi-arrow-right arrow"></i>
                <span class="compact-text to">{{ truncate(output.parsed.refined_hypothesis_text, 40) }}</span>
            </div>

            <div class="expand-toggle" @click="expanded = !expanded">
                <span>{{ expanded ? 'Hide' : 'Show' }} Details</span>
                <i :class="expanded ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"></i>
            </div>
        </div>

        <!-- Expanded view: full details -->
        <div v-if="expanded" class="expanded-content">
            <div v-if="output.parsed.original_hypothesis_text" class="evolution-full">
                <div class="evolution-item from">
                    <span class="label">Original:</span>
                    <span class="text">{{ output.parsed.original_hypothesis_text }}</span>
                </div>
                <i class="pi pi-arrow-down arrow-vertical"></i>
                <div class="evolution-item to">
                    <span class="label">Refined:</span>
                    <span class="text">{{ output.parsed.refined_hypothesis_text }}</span>
                </div>
            </div>

            <div v-if="output.parsed.refinement_summary" class="refinement-summary">
                <strong>Refinement Summary:</strong>
                <p>{{ output.parsed.refinement_summary }}</p>
            </div>

            <div v-if="output.parsed.specific_refinements && output.parsed.specific_refinements.length > 0" class="refinements">
                <strong>Key Changes:</strong>
                <ul>
                    <li v-for="(ref, i) in output.parsed.specific_refinements" :key="i">
                        <span class="aspect">{{ formatAspect(ref.aspect) }}:</span> {{ ref.change }}
                    </li>
                </ul>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface AgentOutput {
    name: string;
    content: string;
    parsed: any;
    timestamp: number;
}

defineProps<{
    output: AgentOutput;
}>();

const expanded = ref(false);

const truncate = (text: string, maxLength: number): string => {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
};

const formatAspect = (aspect: string): string => {
    return aspect
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
};
</script>

<style lang="scss" scoped>
.evolver-agent {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    font-size: 0.75rem;

    .compact-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .evolution-compact {
        display: flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.375rem 0.5rem;
        background: var(--p-surface-100);
        border-radius: 4px;
        font-size: 0.75rem;
        flex: 1;

        .compact-text {
            color: var(--p-text-color);
            font-style: italic;
            line-height: 1.3;

            &.from {
                opacity: 0.7;
            }

            &.to {
                font-weight: 600;
            }
        }

        .arrow {
            color: var(--p-primary-color);
            font-size: 0.8rem;
            flex-shrink: 0;
        }
    }

    .expand-toggle {
        display: flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.25rem 0.5rem;
        background: var(--p-surface-100);
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.75rem;
        color: var(--p-primary-color);
        font-weight: 500;
        transition: background 0.2s;
        flex-shrink: 0;

        &:hover {
            background: var(--p-surface-200);
        }

        i {
            font-size: 0.7rem;
        }
    }

    .expanded-content {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        padding-top: 0.5rem;
        border-top: 1px solid var(--p-surface-border);

        strong {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--p-text-color-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: block;
            margin-bottom: 0.25rem;
        }

        p {
            margin: 0;
            line-height: 1.5;
            color: var(--p-text-color-secondary);
            font-size: 0.8rem;
        }
    }

    .evolution-full {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        padding: 0.5rem;
        background: var(--p-surface-100);
        border-radius: 4px;

        .evolution-item {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;

            .label {
                font-weight: 600;
                color: var(--p-text-color-secondary);
                font-size: 0.7rem;
                text-transform: uppercase;
            }

            .text {
                color: var(--p-text-color);
                line-height: 1.3;
                font-style: italic;
                font-size: 0.8rem;
            }
        }

        .from {
            opacity: 0.7;
        }

        .to {
            font-weight: 500;
        }

        .arrow-vertical {
            color: var(--p-primary-color);
            font-size: 1rem;
            align-self: center;
        }
    }

    .refinements {
        ul {
            margin: 0;
            padding-left: 1.25rem;
            font-size: 0.8rem;
            line-height: 1.4;
            color: var(--p-text-color-secondary);

            li {
                margin: 0.25rem 0;

                .aspect {
                    font-weight: 600;
                    color: var(--p-primary-color);
                }
            }
        }
    }
}
</style>
