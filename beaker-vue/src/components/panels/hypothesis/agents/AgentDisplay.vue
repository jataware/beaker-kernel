<template>
    <div class="agent-display">
        <SupervisorAgent v-if="output.name === 'Supervisor'" :output="output" />
        <HypothesisGeneratorAgent v-else-if="output.name === 'HypothesisGenerator'" :output="output" />
        <HypothesisReflectorAgent v-else-if="output.name === 'HypothesisReflector'" :output="output" />
        <HypothesisRankerAgent v-else-if="output.name === 'HypothesisRanker'" :output="output" />
        <TournamentJudgeAgent v-else-if="output.name === 'TournamentJudge'" :output="output" />
        <MetaReviewerAgent v-else-if="output.name === 'MetaReviewer'" :output="output" />
        <HypothesisEvolverAgent v-else-if="output.name === 'HypothesisEvolver'" :output="output" />
        <ProximityAnalyzerAgent v-else-if="output.name === 'ProximityAnalyzer'" :output="output" />
        <div v-else class="fallback-agent">
            <pre class="raw-output">{{ output.content }}</pre>
        </div>
    </div>
</template>

<script setup lang="ts">
import SupervisorAgent from './SupervisorAgent.vue';
import HypothesisGeneratorAgent from './HypothesisGeneratorAgent.vue';
import HypothesisReflectorAgent from './HypothesisReflectorAgent.vue';
import HypothesisRankerAgent from './HypothesisRankerAgent.vue';
import TournamentJudgeAgent from './TournamentJudgeAgent.vue';
import MetaReviewerAgent from './MetaReviewerAgent.vue';
import HypothesisEvolverAgent from './HypothesisEvolverAgent.vue';
import ProximityAnalyzerAgent from './ProximityAnalyzerAgent.vue';

interface AgentOutput {
    name: string;
    content: string;
    parsed: any;
    timestamp: number;
    phase?: string;
    iteration?: number;
}

defineProps<{
    output: AgentOutput;
}>();
</script>

<style lang="scss" scoped>
.fallback-agent {
    padding: 0.5rem;
}

.raw-output {
    margin: 0;
    padding: 0.5rem;
    background: #1e1e1e;
    border-radius: 4px;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 0.7rem;
    line-height: 1.4;
    color: #d4d4d4;
    overflow-x: auto;
    white-space: pre-wrap;
    max-height: 200px;
    overflow-y: auto;
}
</style>
