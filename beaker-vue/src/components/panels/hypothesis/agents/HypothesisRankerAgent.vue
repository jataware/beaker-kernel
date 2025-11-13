<template>
    <div v-if="output.parsed && output.parsed.ranked_hypotheses" class="ranker-agent">
        <strong>Top {{ output.parsed.ranked_hypotheses.length }} Ranked Hypotheses</strong>
        <div class="ranked-list">
            <div
                v-for="(ranked, i) in visibleHypotheses"
                :key="i"
                class="ranked-item"
            >
                <span class="rank-badge">{{ i + 1 }}</span>
                <span class="rank-text">{{ ranked.text }}</span>
                <span v-if="ranked.overall_score !== undefined" class="rank-score">
                    {{ (ranked.overall_score * 100).toFixed(0) }}%
                </span>
            </div>
        </div>

        <div v-if="hasMore" class="expand-toggle" @click="showAll = !showAll">
            <span>{{ showAll ? 'Show Less' : `Show All ${output.parsed.ranked_hypotheses.length}` }}</span>
            <i :class="showAll ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"></i>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface AgentOutput {
    name: string;
    content: string;
    parsed: any;
    timestamp: number;
}

const props = defineProps<{
    output: AgentOutput;
    defaultShowCount?: number;
}>();

const showAll = ref(false);
const defaultShowCount = computed(() => props.defaultShowCount || 3);

const visibleHypotheses = computed(() => {
    if (!props.output.parsed?.ranked_hypotheses) return [];
    if (showAll.value) {
        return props.output.parsed.ranked_hypotheses;
    }
    return props.output.parsed.ranked_hypotheses.slice(0, defaultShowCount.value);
});

const hasMore = computed(() => {
    return props.output.parsed?.ranked_hypotheses?.length > defaultShowCount.value;
});

const truncateText = (text: string, maxLength: number): string => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
};
</script>

<style lang="scss" scoped>
.ranker-agent {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;

    strong {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--p-text-color);
    }

    .ranked-list {
        display: flex;
        flex-direction: column;
        gap: 0.375rem;
    }

    .ranked-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.375rem 0.5rem;
        background: var(--p-surface-100);
        border-radius: 4px;
        font-size: 0.8rem;

        .rank-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 20px;
            height: 20px;
            background: var(--p-primary-color);
            color: white;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            flex-shrink: 0;
        }

        .rank-text {
            flex: 1;
            color: var(--p-text-color);
            line-height: 1.3;
        }

        .rank-score {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--p-primary-color);
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
        align-self: flex-start;
        transition: background 0.2s;

        &:hover {
            background: var(--p-surface-200);
        }

        i {
            font-size: 0.7rem;
        }
    }
}
</style>
