<template>
    <div v-if="output.parsed && output.parsed.hypotheses" class="generator-agent">
        <strong>Generated {{ output.parsed.hypotheses.length }} Hypotheses</strong>
        <ol class="hypothesis-list">
            <li v-for="(hyp, i) in visibleHypotheses" :key="i">{{ hyp.text }}</li>
        </ol>

        <div v-if="hasMore" class="expand-toggle" @click="showAll = !showAll">
            <span>{{ showAll ? 'Show Less' : `Show All ${output.parsed.hypotheses.length}` }}</span>
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
    if (!props.output.parsed?.hypotheses) return [];
    if (showAll.value) {
        return props.output.parsed.hypotheses;
    }
    return props.output.parsed.hypotheses.slice(0, defaultShowCount.value);
});

const hasMore = computed(() => {
    return props.output.parsed?.hypotheses?.length > defaultShowCount.value;
});
</script>

<style lang="scss" scoped>
.generator-agent {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;

    strong {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--p-text-color);
    }

    .hypothesis-list {
        margin: 0;
        padding-left: 1.25rem;
        font-size: 0.8rem;
        line-height: 1.4;
        color: var(--p-text-color-secondary);

        li {
            margin: 0.375rem 0;
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
