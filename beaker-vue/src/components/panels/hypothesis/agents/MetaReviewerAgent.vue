<template>
    <div v-if="output.parsed" class="meta-reviewer-agent">
        <!-- Compact view: just the summary -->
        <div v-if="output.parsed.meta_review_summary" class="summary-compact">
            <p>{{ truncate(output.parsed.meta_review_summary, 120) }}</p>
        </div>

        <div class="expand-toggle" @click="expanded = !expanded">
            <span>{{ expanded ? 'Hide' : 'Show' }} Details</span>
            <i :class="expanded ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"></i>
        </div>

        <!-- Expanded view: all details -->
        <div v-if="expanded" class="expanded-content">
            <div v-if="output.parsed.meta_review_summary" class="summary-full">
                <strong>Full Summary:</strong>
                <p>{{ output.parsed.meta_review_summary }}</p>
            </div>

            <div v-if="output.parsed.recurring_themes && output.parsed.recurring_themes.length > 0" class="themes">
                <strong>Recurring Themes:</strong>
                <ul>
                    <li v-for="(theme, i) in output.parsed.recurring_themes" :key="i">
                        <span class="theme-name">{{ theme.theme }}</span>
                        <span v-if="theme.frequency" class="theme-freq">({{ theme.frequency }})</span>
                    </li>
                </ul>
            </div>

            <div v-if="output.parsed.strategic_recommendations && output.parsed.strategic_recommendations.length > 0" class="recommendations">
                <strong>Strategic Recommendations:</strong>
                <ul>
                    <li v-for="(rec, i) in output.parsed.strategic_recommendations" :key="i">
                        {{ rec.recommendation || rec }}
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
</script>

<style lang="scss" scoped>
.meta-reviewer-agent {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    font-size: 0.85rem;

    .summary-compact {
        p {
            margin: 0;
            line-height: 1.5;
            color: var(--p-text-color);
            font-size: 0.8rem;
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
        align-self: flex-start;
        transition: background 0.2s;

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

    .themes, .recommendations {
        ul {
            margin: 0;
            padding-left: 1.25rem;
            font-size: 0.8rem;
            line-height: 1.4;
            color: var(--p-text-color-secondary);

            li {
                margin: 0.25rem 0;

                .theme-name {
                    font-weight: 600;
                    color: var(--p-text-color);
                }

                .theme-freq {
                    font-size: 0.75rem;
                    color: var(--p-text-color-secondary);
                    margin-left: 0.25rem;
                }
            }
        }
    }
}
</style>
