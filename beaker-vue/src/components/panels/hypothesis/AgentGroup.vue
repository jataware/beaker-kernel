<template>
    <div class="agent-group">
        <div class="agent-group-header" @click="toggleExpanded">
            <i :class="iconClass" :style="{ color: iconColor }"></i>
            <span class="agent-name">{{ formattedAgentName }}</span>
            <span class="agent-count-badge">{{ agents.length }}</span>
            <span class="agent-summary">{{ summary }}</span>
            <i :class="isExpanded ? 'pi pi-chevron-up' : 'pi pi-chevron-down'" class="expand-icon"></i>
        </div>

        <div v-if="isExpanded" class="agent-group-content">
            <div
                v-for="(agent, index) in agents"
                :key="index"
                class="grouped-agent-item"
            >
                <div class="grouped-agent-header">
                    <i :class="iconClass" :style="{ color: iconColor }"></i>
                    <span class="agent-label">{{ formattedAgentName }} {{ index + 1 }}</span>
                    <span class="agent-time">{{ formatTimestamp(agent.timestamp) }}</span>
                </div>
                <div class="grouped-agent-content">
                    <slot :agent="agent" :index="index"></slot>
                </div>
            </div>
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
    agentName: string;
    agents: AgentOutput[];
    summary: string;
}>();

const isExpanded = ref(false);

const toggleExpanded = () => {
    isExpanded.value = !isExpanded.value;
};

const iconClass = computed(() => {
    const iconMap: Record<string, string> = {
        'HypothesisReflector': 'pi pi-eye',
        'TournamentJudge': 'pi pi-trophy',
    };
    return iconMap[props.agentName] || 'pi pi-cog';
});

const iconColor = computed(() => {
    const colorMap: Record<string, string> = {
        'HypothesisReflector': '#ff9500',
        'TournamentJudge': '#ff3b30',
    };
    return colorMap[props.agentName] || 'var(--p-primary-color)';
});

const formattedAgentName = computed(() => {
    const nameMap: Record<string, string> = {
        'HypothesisReflector': 'Peer Reviewer',
        'TournamentJudge': 'Tournament Judge',
    };
    return nameMap[props.agentName] || props.agentName;
});

const formatTimestamp = (timestamp: number): string => {
    return new Date(timestamp).toLocaleTimeString();
};
</script>

<style lang="scss" scoped>
.agent-group {
    border: 1px solid var(--p-surface-border);
    border-radius: 6px;
    overflow: hidden;
    background: var(--p-surface-0);
}

.agent-group-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0.75rem;
    background: var(--p-surface-100);
    cursor: pointer;
    transition: background 0.2s;

    &:hover {
        background: var(--p-surface-200);
    }

    i {
        font-size: 0.9rem;
    }

    .agent-name {
        font-weight: 500;
        font-size: 0.85rem;
        color: var(--p-text-color);
    }

    .agent-count-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 20px;
        height: 20px;
        padding: 0 0.4rem;
        background: var(--p-primary-color);
        color: white;
        border-radius: 10px;
        font-size: 0.7rem;
        font-weight: 600;
    }

    .agent-summary {
        flex: 1;
        font-size: 0.75rem;
        color: var(--p-text-color-secondary);
    }

    .expand-icon {
        font-size: 0.8rem;
        color: var(--p-text-color-secondary);
    }
}

.agent-group-content {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.5rem;
}

.grouped-agent-item {
    border: 1px solid var(--p-surface-border);
    border-radius: 4px;
    overflow: hidden;
    background: var(--p-surface-50);
}

.grouped-agent-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.5rem;
    background: var(--p-surface-100);
    border-bottom: 1px solid var(--p-surface-border);

    i {
        font-size: 0.8rem;
        color: var(--p-text-color-secondary);
    }

    .agent-label {
        flex: 1;
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--p-text-color);
    }

    .agent-time {
        font-size: 0.7rem;
        color: var(--p-text-color-secondary);
        font-family: monospace;
    }
}

.grouped-agent-content {
    padding: 0.5rem;
}
</style>
