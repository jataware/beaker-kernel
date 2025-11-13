<template>
    <div v-if="agentOutputs.length > 0" class="agent-activity-section">
        <Divider />

        <PhaseNavigation
            :phases="phases"
            :selected-phase-id="selectedPhaseId"
            @select-phase="scrollToPhase"
        />

        <h4 class="section-title">Agent Activity ({{ agentOutputs.length }})</h4>

        <div class="phase-groups">
            <PhaseGroup
                v-for="(phase, index) in phases"
                :key="phase.id"
                :ref="el => setPhaseRef(phase.id, el)"
                :phase="phase"
                :agent-count="phase.agentCount"
                :default-expanded="index === phases.length - 1"
                @toggle="onPhaseToggle"
            >
                <template v-for="(item, itemIndex) in groupAgentsByType(phase.agents)" :key="itemIndex">
                    <!-- Agent Group (multiple similar agents) -->
                    <AgentGroup
                        v-if="'agents' in item"
                        :agent-name="item.name"
                        :agents="item.agents"
                        :summary="item.summary"
                    >
                        <template #default="{ agent }">
                            <AgentDisplay :output="agent" />
                        </template>
                    </AgentGroup>

                    <!-- Individual Agent -->
                    <div v-else-if="!item.isPhaseMarker" class="individual-agent">
                        <div class="agent-header">
                            <i :class="getAgentIcon(item.name)" :style="{ color: getAgentColor(item.name) }"></i>
                            <span class="agent-name">{{ formatAgentName(item.name) }}</span>
                            <span class="agent-time">{{ formatTimestamp(item.timestamp) }}</span>
                        </div>
                        <div class="agent-content">
                            <AgentDisplay :output="item" />
                        </div>
                    </div>
                </template>
            </PhaseGroup>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import Divider from 'primevue/divider';
import PhaseNavigation from './PhaseNavigation.vue';
import PhaseGroup from './PhaseGroup.vue';
import AgentGroup from './AgentGroup.vue';
import AgentDisplay from './agents/AgentDisplay.vue';

interface AgentOutput {
    name: string;
    content: string;
    parsed: any;
    timestamp: number;
    isPhaseMarker?: boolean;
    description?: string;
    phase?: string;
    iteration?: number;
}

interface PhaseInfo {
    id: string;
    name: string;
    color: string;
    icon: string;
    agents: AgentOutput[];
    agentCount: number;
    summary: string;
}

interface AgentGroup {
    name: string;
    agents: AgentOutput[];
    summary: string;
}

const props = defineProps<{
    agentOutputs: AgentOutput[];
}>();

const selectedPhaseId = ref<string | null>(null);
const phaseRefs = ref<Map<string, any>>(new Map());

const phases = computed<PhaseInfo[]>(() => {
    const groups: { [key: string]: PhaseInfo } = {};

    props.agentOutputs.forEach((output) => {
        let phaseKey = 'initial_generation';
        let phaseName = 'Initial Generation';
        let phaseColor = '#34c759';
        let phaseIcon = 'pi-sparkles';

        if (output.phase?.includes('tournament')) {
            phaseKey = 'tournament';
            phaseName = 'Tournament Selection';
            phaseColor = '#007aff';
            phaseIcon = 'pi-trophy';
        } else if (output.phase?.startsWith('iteration_')) {
            phaseKey = output.phase;
            const iterNum = output.iteration || 1;
            phaseName = `Iteration ${iterNum}`;
            const colors = ['#af52de', '#ff9500', '#ff3b30', '#5856d6'];
            phaseColor = colors[(iterNum - 1) % colors.length];
            phaseIcon = 'pi-sync';
        }

        if (!groups[phaseKey]) {
            groups[phaseKey] = {
                id: phaseKey,
                name: phaseName,
                color: phaseColor,
                icon: phaseIcon,
                agents: [],
                agentCount: 0,
                summary: ''
            };
        }

        groups[phaseKey].agents.push(output);
    });

    // Generate summaries
    Object.values(groups).forEach(group => {
        const nonMarkerAgents = group.agents.filter(a => !a.isPhaseMarker);
        group.agentCount = nonMarkerAgents.length;

        const agentCounts: { [key: string]: number } = {};
        nonMarkerAgents.forEach(agent => {
            agentCounts[agent.name] = (agentCounts[agent.name] || 0) + 1;
        });

        const summaryParts: string[] = [];
        Object.entries(agentCounts).forEach(([name, count]) => {
            if (count > 1) {
                summaryParts.push(`${count}× ${formatAgentName(name)}`);
            } else {
                summaryParts.push(formatAgentName(name));
            }
        });

        group.summary = summaryParts.slice(0, 3).join(', ') + (summaryParts.length > 3 ? '...' : '');
    });

    return Object.values(groups);
});

const groupAgentsByType = (agents: AgentOutput[]): (AgentOutput | AgentGroup)[] => {
    type ResultItem = (AgentOutput | AgentGroup) & { _earliestTimestamp?: number };
    const result: ResultItem[] = [];
    const grouped: { [key: string]: { agents: AgentOutput[], firstIndex: number } } = {};
    let currentIndex = 0;

    agents.forEach(agent => {
        if (agent.isPhaseMarker) {
            // Skip phase markers
        } else if (agent.name === 'HypothesisReflector' || agent.name === 'TournamentJudge') {
            if (!grouped[agent.name]) {
                grouped[agent.name] = {
                    agents: [],
                    firstIndex: currentIndex
                };
            }
            grouped[agent.name].agents.push(agent);
            currentIndex++;
        } else {
            const item = agent as ResultItem;
            item._earliestTimestamp = agent.timestamp;
            result.push(item);
            currentIndex++;
        }
    });

    // Add grouped agents at their first occurrence position
    Object.entries(grouped).forEach(([name, { agents: groupedAgents, firstIndex }]) => {
        if (groupedAgents.length > 2) {
            let summary = '';
            if (name === 'HypothesisReflector') {
                const scores = groupedAgents
                    .map(a => a.parsed?.overall_score)
                    .filter(s => s !== undefined);
                const avgScore = scores.length > 0
                    ? (scores.reduce((a, b) => a + b, 0) / scores.length * 10).toFixed(1)
                    : 'N/A';
                summary = `${groupedAgents.length} peer reviews (avg: ${avgScore}%)`;
            } else if (name === 'TournamentJudge') {
                summary = `${groupedAgents.length} tournament rounds`;
            }

            const groupItem = {
                name,
                agents: groupedAgents,
                summary,
                _earliestTimestamp: groupedAgents[0].timestamp
            } as ResultItem;
            result.push(groupItem);
        } else {
            groupedAgents.forEach(agent => {
                const item = agent as ResultItem;
                item._earliestTimestamp = agent.timestamp;
                result.push(item);
            });
        }
    });

    // Sort by earliest timestamp to maintain temporal order
    result.sort((a, b) => (a._earliestTimestamp || 0) - (b._earliestTimestamp || 0));

    // Clean up temporary property
    result.forEach(item => delete item._earliestTimestamp);

    return result;
};

const setPhaseRef = (phaseId: string, el: any) => {
    if (el) {
        phaseRefs.value.set(phaseId, el);
    }
};

const scrollToPhase = (phaseId: string) => {
    selectedPhaseId.value = phaseId;
    const phaseRef = phaseRefs.value.get(phaseId);
    if (phaseRef) {
        phaseRef.expand();
        setTimeout(() => {
            const element = document.querySelector(`[data-phase-id="${phaseId}"]`);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 100);
    }
};

const onPhaseToggle = (phaseId: string, expanded: boolean) => {
    if (expanded) {
        selectedPhaseId.value = phaseId;
    }
};

const getAgentIcon = (name: string): string => {
    const iconMap: Record<string, string> = {
        'Supervisor': 'pi pi-star-fill',
        'HypothesisGenerator': 'pi pi-sparkles',
        'HypothesisReflector': 'pi pi-eye',
        'HypothesisRanker': 'pi pi-chart-bar',
        'TournamentJudge': 'pi pi-trophy',
        'MetaReviewer': 'pi pi-book',
        'HypothesisEvolver': 'pi pi-replay',
        'ProximityAnalyzer': 'pi pi-sitemap',
    };
    return iconMap[name] || 'pi pi-cog';
};

const getAgentColor = (name: string): string => {
    const colorMap: Record<string, string> = {
        'Supervisor': '#ffd700',
        'HypothesisGenerator': '#00d4ff',
        'HypothesisReflector': '#ff9500',
        'HypothesisRanker': '#34c759',
        'TournamentJudge': '#ff3b30',
        'MetaReviewer': '#5856d6',
        'HypothesisEvolver': '#af52de',
        'ProximityAnalyzer': '#32ade6',
    };
    return colorMap[name] || 'var(--p-primary-color)';
};

const formatAgentName = (name: string): string => {
    const nameMap: Record<string, string> = {
        'Supervisor': 'Research Supervisor',
        'HypothesisGenerator': 'Hypothesis Generator',
        'HypothesisReflector': 'Peer Reviewer',
        'HypothesisRanker': 'Hypothesis Ranker',
        'TournamentJudge': 'Tournament Judge',
        'MetaReviewer': 'Meta Reviewer',
        'HypothesisEvolver': 'Hypothesis Evolver',
        'ProximityAnalyzer': 'Proximity Analyzer',
    };
    return nameMap[name] || name;
};

const formatTimestamp = (timestamp: number): string => {
    return new Date(timestamp).toLocaleTimeString();
};
</script>

<style lang="scss" scoped>
.agent-activity-section {
    margin-top: 0.5rem;

    .section-title {
        margin: 0 0 0.75rem 0;
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--p-text-color);
    }

    .phase-groups {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
}

.individual-agent {
    border: 1px solid var(--p-surface-border);
    border-radius: 6px;
    overflow: hidden;
    background: var(--p-surface-0);

    .agent-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.5rem 0.75rem;
        background: var(--p-surface-100);
        border-bottom: 1px solid var(--p-surface-border);

        i {
            font-size: 0.9rem;
        }

        .agent-name {
            flex: 1;
            font-weight: 500;
            font-size: 0.85rem;
            color: var(--p-text-color);
        }

        .agent-time {
            font-size: 0.7rem;
            color: var(--p-text-color-secondary);
            font-family: monospace;
        }
    }

    .agent-content {
        padding: 0.75rem;
    }
}
</style>
