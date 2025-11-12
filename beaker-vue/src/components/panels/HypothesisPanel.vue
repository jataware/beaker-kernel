<template>
    <div class="hypothesis-panel">
        <div class="hypothesis-controls">
            <!-- Compact header when generating -->
            <GeneratingHeader
                v-if="isGenerating"
                :research-goal="researchGoal"
                :progress="progress"
                :progress-message="progressMessage"
                @cancel="cancelGeneration"
            />

            <!-- Full input form when not generating -->
            <div v-else class="input-form">
                <h3>Scientific Hypothesis Generation</h3>
                <p class="help-text">
                    Generate scientific hypotheses using AI-CoScientist. This process takes 10-15 minutes.
                </p>
                <Message severity="info" :closable="false" class="attribution-message">
                    Based on <a href="https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/" target="_blank">AI co-scientist</a>, a multi-agent AI system developed by Google Research
                    (<a href="https://arxiv.org/abs/2502.18864" target="_blank">paper</a>).
                </Message>

                <div class="input-section">
                    <label for="research-goal">Research Goal</label>
                    <Textarea
                        id="research-goal"
                        v-model="researchGoal"
                        :placeholder="'Enter your research question or goal...\n\nExample: How do regulatory T cells suppress immune responses in autoimmune diseases?'"
                        :autoResize="true"
                        :rows="5"
                        class="research-goal-input"
                    />
                </div>

                <Button
                    @click="generateHypotheses"
                    :disabled="!researchGoal"
                    label="Generate Hypotheses"
                    icon="pi pi-sparkles"
                    class="generate-button"
                />
            </div>

            <!-- Agent Activity Section -->
            <AgentActivitySection :agent-outputs="agentOutputs" />

            <Message v-if="errorMessage" severity="error" :closable="true" @close="errorMessage = ''">
                {{ errorMessage }}
            </Message>
        </div>

        <!-- Results Section -->
        <div v-if="hypotheses.length > 0" class="results-section">
            <Divider />
            <h4>Generated Hypotheses ({{ hypotheses.length }})</h4>
            <p class="results-meta" v-if="executionTime">
                Generated in {{ formatTime(executionTime) }}
            </p>

            <div class="hypothesis-list">
                <HypothesisCard
                    v-for="(hypothesis, index) in hypotheses"
                    :key="index"
                    :hypothesis="hypothesis"
                    :rank="index + 1"
                />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, inject, onUnmounted } from "vue";
import type { BeakerSessionComponentType } from '../session/BeakerSession.vue';
import Button from "primevue/button";
import Textarea from "primevue/textarea";
import Message from "primevue/message";
import Divider from "primevue/divider";
import GeneratingHeader from "./hypothesis/GeneratingHeader.vue";
import AgentActivitySection from "./hypothesis/AgentActivitySection.vue";
import HypothesisCard from "./HypothesisCard.vue";

interface Hypothesis {
    text: string;
    score: number;
    elo_rating: number;
    reviews: any[];
    similarity_cluster_id?: string;
    evolution_history: string[];
    win_count: number;
    loss_count: number;
}

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

const beakerSession = inject<BeakerSessionComponentType>("beakerSession");

const researchGoal = ref<string>("");
const isGenerating = ref<boolean>(false);
const progress = ref<number>(0);
const progressMessage = ref<string>("");
const errorMessage = ref<string>("");
const hypotheses = ref<Hypothesis[]>([]);
const executionTime = ref<number>(0);
const currentTaskId = ref<string>("");
const agentOutputs = ref<AgentOutput[]>([]);

let messageHookDisconnect: (() => void) | null = null;

const generateHypotheses = async () => {
    if (!researchGoal.value || !beakerSession) {
        return;
    }

    // Reset state
    isGenerating.value = true;
    progress.value = 0;
    progressMessage.value = "Starting hypothesis generation...";
    errorMessage.value = "";
    hypotheses.value = [];
    executionTime.value = 0;
    agentOutputs.value = [];

    try {
        // Listen for hypothesis messages via window events
        const hypothesisMessageHandler = (event: Event) => {
            const customEvent = event as CustomEvent;
            const { type, content } = customEvent.detail;

            if (type === "hypothesis_progress") {
                const { phase, message: phaseMsg, progress: phaseProgress, agent_output, agent_name, description, iteration } = content;
                progressMessage.value = phaseMsg || `Phase: ${phase}`;
                if (phaseProgress !== undefined) {
                    progress.value = phaseProgress;
                }

                // Check if this is a phase marker (has description field)
                if (description) {
                    const phaseMarkerEntry = {
                        name: "PhaseMarker",
                        content: phaseMsg,
                        parsed: {},
                        timestamp: Date.now(),
                        isPhaseMarker: true,
                        description: description,
                        phase: phase,
                        iteration: iteration
                    };
                    agentOutputs.value.push(phaseMarkerEntry);
                }

                // Capture agent outputs
                if (agent_output && agent_name) {
                    let formattedContent = agent_output;
                    let parsed: any = {};

                    try {
                        // Strip markdown code fences if present
                        let cleanOutput = agent_output.trim();
                        if (cleanOutput.startsWith('```json') || cleanOutput.startsWith('```')) {
                            const lines = cleanOutput.split('\n');
                            if (lines[0].startsWith('```')) {
                                lines.shift();
                            }
                            if (lines[lines.length - 1].trim() === '```') {
                                lines.pop();
                            }
                            cleanOutput = lines.join('\n').trim();
                        }

                        // Try to parse the JSON
                        try {
                            parsed = JSON.parse(cleanOutput);
                        } catch (parseError) {
                            // Try to extract first valid JSON object
                            const firstBrace = cleanOutput.indexOf('{');
                            if (firstBrace === -1) throw parseError;

                            let braceCount = 0;
                            let endPos = -1;
                            for (let i = firstBrace; i < cleanOutput.length; i++) {
                                if (cleanOutput[i] === '{') braceCount++;
                                else if (cleanOutput[i] === '}') {
                                    braceCount--;
                                    if (braceCount === 0) {
                                        endPos = i + 1;
                                        break;
                                    }
                                }
                            }

                            if (endPos > 0) {
                                const firstJsonObject = cleanOutput.substring(firstBrace, endPos);
                                parsed = JSON.parse(firstJsonObject);
                                console.warn(`⚠️ Extracted first JSON object from concatenated output for ${agent_name}`);
                            } else {
                                throw parseError;
                            }
                        }

                        formattedContent = JSON.stringify(parsed, null, 2);
                    } catch (e) {
                        console.error(`❌ Failed to parse ${agent_name} output:`, e);
                    }

                    const outputEntry = {
                        name: agent_name,
                        content: formattedContent,
                        parsed,
                        timestamp: Date.now(),
                        phase: phase,
                        iteration: iteration
                    };
                    agentOutputs.value.push(outputEntry);
                }
            } else if (type === "hypothesis_complete") {
                const { result } = content;
                hypotheses.value = result.hypotheses || [];
                executionTime.value = result.execution_time || 0;
                isGenerating.value = false;
                progress.value = 100;
                progressMessage.value = "Complete!";
            } else if (type === "hypothesis_error") {
                const { error } = content;
                errorMessage.value = `Error: ${error}`;
                isGenerating.value = false;
                progress.value = 0;
            } else if (type === "hypothesis_cancelled") {
                progressMessage.value = "Generation cancelled";
                isGenerating.value = false;
                progress.value = 0;
            }
        };

        // Add event listener
        window.addEventListener('hypothesis-message', hypothesisMessageHandler);

        // Store cleanup function
        messageHookDisconnect = () => {
            window.removeEventListener('hypothesis-message', hypothesisMessageHandler);
        };

        // Execute the action
        const future = beakerSession.session.executeAction("generate_hypotheses", {
            research_goal: researchGoal.value,
            config: {}
        });

        // Handle response
        future.onResponse = async (msg: any) => {
            const { status, task_id, error } = msg.content;

            if (status === "started") {
                currentTaskId.value = task_id;
                progressMessage.value = "Hypothesis generation started...";
            } else if (status === "error") {
                errorMessage.value = error || "Failed to start hypothesis generation";
                isGenerating.value = false;
            }
        };

    } catch (error) {
        console.error("Error starting hypothesis generation:", error);
        errorMessage.value = `Failed to start generation: ${error}`;
        isGenerating.value = false;
    }
};

const cancelGeneration = async () => {
    if (!currentTaskId.value || !beakerSession) {
        return;
    }

    try {
        const future = beakerSession.session.executeAction("cancel_hypothesis_generation", {
            task_id: currentTaskId.value
        });

        future.onResponse = async (msg: any) => {
            const { status } = msg.content;
            if (status === "cancelled") {
                isGenerating.value = false;
                progressMessage.value = "Cancelled";
            }
        };
    } catch (error) {
        console.error("Error cancelling generation:", error);
    }
};

const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
};

onUnmounted(() => {
    if (messageHookDisconnect) {
        messageHookDisconnect();
    }
});
</script>

<style lang="scss" scoped>
.hypothesis-panel {
    padding: 1rem;
    height: 100%;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.hypothesis-controls {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.input-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;

    h3 {
        margin: 0;
        color: var(--p-primary-color);
    }

    .help-text {
        margin: 0;
        color: var(--p-text-color-secondary);
        font-size: 0.875rem;
    }

    .attribution-message {
        font-size: 0.8rem;

        :deep(a) {
            color: var(--p-primary-color);
            text-decoration: none;
            font-weight: 500;

            &:hover {
                text-decoration: underline;
            }
        }
    }
}

.input-section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;

    label {
        font-weight: 600;
        font-size: 0.875rem;
    }

    .research-goal-input {
        width: 100%;
        font-family: var(--p-font-family);
    }
}

.generate-button {
    width: 100%;
}

.results-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;

    h4 {
        margin: 0;
    }

    .results-meta {
        margin: 0;
        font-size: 0.875rem;
        color: var(--p-text-color-secondary);
    }
}

.hypothesis-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}
</style>
