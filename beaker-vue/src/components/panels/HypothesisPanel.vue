<template>
    <div class="hypothesis-panel">
        <div class="hypothesis-controls">
            <!-- Compact header when generating -->
            <div v-if="isGenerating" class="generating-header">
                <div class="header-row">
                    <div class="title-section">
                        <h3>Generating Hypotheses</h3>
                        <p class="compact-goal">{{ researchGoal }}</p>
                    </div>
                    <Button
                        @click="cancelGeneration"
                        label="Cancel"
                        icon="pi pi-times"
                        severity="danger"
                        text
                        class="cancel-button-compact"
                    />
                </div>
                <ProgressBar :value="progress" :showValue="false" class="progress-bar" />
                <div class="progress-message">
                    <i class="pi pi-spin pi-spinner"></i>
                    {{ progressMessage }}
                </div>
            </div>

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
            <div v-if="agentOutputs.length > 0" class="agent-outputs">
                <Divider />
                <h4 class="section-title">Agent Activity ({{ agentOutputs.length }})</h4>
                <Accordion :value="[agentOutputs.length - 1]" class="agent-accordion">
                    <AccordionPanel
                        v-for="(output, index) in agentOutputs"
                        :key="index"
                        :value="index"
                    >
                        <template #header>
                            <div class="accordion-header" :class="{ 'phase-marker-header': output.isPhaseMarker }">
                                <i v-if="output.isPhaseMarker" class="pi pi-flag-fill" style="color: #ff3b30;"></i>
                                <i v-else-if="output.name === 'Supervisor'" class="pi pi-star-fill" style="color: #ffd700;"></i>
                                <i v-else-if="output.name === 'HypothesisGenerator'" class="pi pi-sparkles" style="color: #00d4ff;"></i>
                                <i v-else-if="output.name === 'HypothesisReflector'" class="pi pi-eye" style="color: #ff9500;"></i>
                                <i v-else-if="output.name === 'HypothesisRanker'" class="pi pi-chart-bar" style="color: #34c759;"></i>
                                <i v-else-if="output.name === 'TournamentJudge'" class="pi pi-trophy" style="color: #ff3b30;"></i>
                                <i v-else-if="output.name === 'MetaReviewer'" class="pi pi-book" style="color: #5856d6;"></i>
                                <i v-else-if="output.name === 'HypothesisEvolver'" class="pi pi-replay" style="color: #af52de;"></i>
                                <i v-else-if="output.name === 'ProximityAnalyzer'" class="pi pi-sitemap" style="color: #32ade6;"></i>
                                <i v-else class="pi pi-cog"></i>
                                <span class="agent-name">{{ output.isPhaseMarker ? output.content : formatAgentName(output.name) }}</span>
                                <span v-if="!output.isPhaseMarker && output.iteration" class="iteration-badge">Iteration {{ output.iteration }}</span>
                                <span class="agent-time">{{ formatTimestamp(output.timestamp) }}</span>
                            </div>
                        </template>

                        <!-- Phase Marker -->
                        <div v-if="output.isPhaseMarker" class="phase-marker-content">
                            <div class="phase-marker-badge">
                                <i class="pi pi-flag-fill"></i>
                                <span>{{ output.content }}</span>
                            </div>
                            <p class="phase-marker-description">{{ output.description }}</p>
                        </div>

                        <!-- Supervisor Agent -->
                        <Panel v-else-if="output.name === 'Supervisor'" header="Supervisor Analysis" :toggleable="true" :collapsed="false" class="agent-panel">
                            <div v-if="output.parsed && output.parsed.research_goal_analysis" class="content-section">
                                <p class="summary">{{ output.parsed.research_goal_analysis.goal_summary }}</p>
                                <div v-if="output.parsed.research_goal_analysis.key_areas" class="key-areas">
                                    <h6>Key Areas</h6>
                                    <ul>
                                        <li v-for="(area, i) in output.parsed.research_goal_analysis.key_areas" :key="i">{{ area }}</li>
                                    </ul>
                                </div>
                            </div>
                            <div v-if="output.parsed && output.parsed.workflow_plan && output.parsed.workflow_plan.generation_phase" class="content-section workflow-section">
                                <h6>Workflow Plan</h6>
                                <div class="workflow-details">
                                    <p><strong>Target:</strong> {{ output.parsed.workflow_plan.generation_phase.quantity_target }} hypotheses</p>
                                    <p><strong>Diversity:</strong> {{ output.parsed.workflow_plan.generation_phase.diversity_targets }}</p>
                                </div>
                            </div>
                        </Panel>

                        <!-- HypothesisGenerator Agent -->
                        <Panel v-else-if="output.name === 'HypothesisGenerator'" header="Generated Hypotheses" :toggleable="true" :collapsed="false" class="agent-panel">
                            <div v-if="output.parsed && output.parsed.hypotheses" class="content-section">
                                <h6>Generated {{ output.parsed.hypotheses.length }} Hypotheses</h6>
                                <ol class="hypothesis-list-compact">
                                    <li v-for="(hyp, i) in output.parsed.hypotheses" :key="i">{{ hyp.text }}</li>
                                </ol>
                            </div>
                        </Panel>

                        <!-- HypothesisReflector Agent -->
                        <Panel v-else-if="output.name === 'HypothesisReflector'" header="Peer Review" :toggleable="true" :collapsed="false" class="agent-panel">
                            <div v-if="output.parsed && output.parsed.hypothesis_text" class="content-section review-hypothesis">
                                <p class="hypothesis-text">{{ output.parsed.hypothesis_text }}</p>
                            </div>
                            <div v-if="output.parsed && output.parsed.review_summary" class="content-section">
                                <h6>Review Summary</h6>
                                <p>{{ output.parsed.review_summary }}</p>
                            </div>
                            <div v-if="output.parsed && output.parsed.overall_score !== undefined" class="content-section">
                                <div class="overall-score">
                                    <span class="score-label">Overall Score</span>
                                    <span class="score-value">{{ (output.parsed.overall_score * 100).toFixed(0) }}%</span>
                                </div>
                            </div>
                            <div v-if="output.parsed && output.parsed.scores" class="content-section">
                                <h6>Detailed Scores</h6>
                                <div class="score-grid">
                                    <div v-for="(value, key) in output.parsed.scores" :key="key" class="score-item">
                                        <span class="score-name">{{ formatScoreName(key) }}</span>
                                        <ProgressBar :value="(value / 5) * 100" :showValue="false" class="score-bar" />
                                        <span class="score-num">{{ value }}/5</span>
                                    </div>
                                </div>
                            </div>
                            <div v-if="output.parsed && output.parsed.constructive_feedback" class="content-section">
                                <h6>Constructive Feedback</h6>
                                <p>{{ output.parsed.constructive_feedback }}</p>
                            </div>
                        </Panel>

                        <!-- HypothesisRanker Agent -->
                        <Panel v-else-if="output.name === 'HypothesisRanker'" header="Ranked Hypotheses" :toggleable="true" :collapsed="false" class="agent-panel">
                            <div v-if="output.parsed && output.parsed.ranked_hypotheses" class="content-section">
                                <h6>Top {{ Math.min(5, output.parsed.ranked_hypotheses.length) }} Ranked Hypotheses</h6>
                                <div class="ranked-list">
                                    <div
                                        v-for="(ranked, i) in output.parsed.ranked_hypotheses.slice(0, 5)"
                                        :key="i"
                                        class="ranked-item"
                                    >
                                        <div class="rank-badge">{{ i + 1 }}</div>
                                        <div class="rank-content">
                                            <p class="rank-hypothesis">{{ ranked.text }}</p>
                                            <p v-if="ranked.ranking_explanation" class="rank-explanation">{{ ranked.ranking_explanation }}</p>
                                            <div v-if="ranked.overall_score !== undefined" class="rank-score">
                                                {{ (ranked.overall_score * 100).toFixed(0) }}%
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </Panel>

                        <!-- TournamentJudge Agent -->
                        <Panel v-else-if="output.name === 'TournamentJudge'" header="Tournament Judgment" :toggleable="true" :collapsed="false" class="agent-panel">
                            <div v-if="output.parsed" class="tournament-content">
                                <div class="tournament-matchup">
                                    <div class="hypothesis-box">
                                        <div class="hypothesis-label">Hypothesis A</div>
                                        <p>{{ output.parsed.hypothesis_a }}</p>
                                    </div>
                                    <div class="vs-divider">VS</div>
                                    <div class="hypothesis-box">
                                        <div class="hypothesis-label">Hypothesis B</div>
                                        <p>{{ output.parsed.hypothesis_b }}</p>
                                    </div>
                                </div>

                                <div v-if="output.parsed.winner" class="winner-section">
                                    <div class="winner-badge">
                                        <i class="pi pi-trophy"></i>
                                        Winner: Hypothesis {{ output.parsed.winner.toUpperCase() }}
                                    </div>
                                    <p v-if="output.parsed.decision_summary" class="decision-summary">
                                        {{ output.parsed.decision_summary }}
                                    </p>
                                </div>

                                <Panel v-if="output.parsed.judgment_explanation" header="Detailed Comparison" :toggleable="true" :collapsed="true" class="judgment-panel">
                                    <div class="comparison-grid">
                                        <div v-for="(value, key) in output.parsed.judgment_explanation" :key="key" class="comparison-item">
                                            <h6>{{ formatScoreName(key) }}</h6>
                                            <p>{{ value }}</p>
                                        </div>
                                    </div>
                                </Panel>
                            </div>
                        </Panel>

                        <!-- MetaReviewer Agent -->
                        <Panel v-else-if="output.name === 'MetaReviewer'" header="Meta Review" :toggleable="true" :collapsed="false" class="agent-panel">
                            <div v-if="output.parsed" class="meta-review-content">
                                <div v-if="output.parsed.meta_review_summary" class="content-section">
                                    <p class="summary">{{ output.parsed.meta_review_summary }}</p>
                                </div>

                                <div v-if="output.parsed.recurring_themes && output.parsed.recurring_themes.length > 0" class="content-section">
                                    <h6>Recurring Themes</h6>
                                    <div class="themes-list">
                                        <div v-for="(theme, i) in output.parsed.recurring_themes" :key="i" class="theme-item">
                                            <div class="theme-header">
                                                <strong>{{ theme.theme }}</strong>
                                                <span class="theme-frequency">{{ theme.frequency }}</span>
                                            </div>
                                            <p>{{ theme.description }}</p>
                                        </div>
                                    </div>
                                </div>

                                <div v-if="output.parsed.strategic_recommendations && output.parsed.strategic_recommendations.length > 0" class="content-section">
                                    <h6>Strategic Recommendations</h6>
                                    <div class="recommendations-list">
                                        <div v-for="(rec, i) in output.parsed.strategic_recommendations" :key="i" class="recommendation-item">
                                            <div class="rec-header">{{ rec.focus_area }}</div>
                                            <p><strong>Recommendation:</strong> {{ rec.recommendation }}</p>
                                            <p class="rec-justification"><strong>Justification:</strong> {{ rec.justification }}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </Panel>

                        <!-- HypothesisEvolver Agent -->
                        <Panel v-else-if="output.name === 'HypothesisEvolver'" header="Hypothesis Evolution" :toggleable="true" :collapsed="false" class="agent-panel">
                            <div v-if="output.parsed" class="evolution-content">
                                <div v-if="output.parsed.original_hypothesis_text" class="content-section evolution-comparison">
                                    <div class="evolution-box original">
                                        <div class="evolution-label">Original Hypothesis</div>
                                        <p>{{ output.parsed.original_hypothesis_text }}</p>
                                    </div>
                                    <div class="evolution-arrow">
                                        <i class="pi pi-arrow-right"></i>
                                    </div>
                                    <div class="evolution-box refined">
                                        <div class="evolution-label">Refined Hypothesis</div>
                                        <p>{{ output.parsed.refined_hypothesis_text }}</p>
                                    </div>
                                </div>

                                <div v-if="output.parsed.refinement_summary" class="content-section">
                                    <h6>Refinement Summary</h6>
                                    <p>{{ output.parsed.refinement_summary }}</p>
                                </div>

                                <div v-if="output.parsed.specific_refinements && output.parsed.specific_refinements.length > 0" class="content-section">
                                    <h6>Specific Changes</h6>
                                    <div class="refinements-list">
                                        <div v-for="(ref, i) in output.parsed.specific_refinements" :key="i" class="refinement-item">
                                            <div class="refinement-aspect">{{ formatScoreName(ref.aspect) }}</div>
                                            <p><strong>Change:</strong> {{ ref.change }}</p>
                                            <p class="refinement-just"><strong>Justification:</strong> {{ ref.justification }}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </Panel>

                        <!-- ProximityAnalyzer Agent -->
                        <Panel v-else-if="output.name === 'ProximityAnalyzer'" header="Similarity Analysis" :toggleable="true" :collapsed="false" class="agent-panel">
                            <div v-if="output.parsed" class="proximity-content">
                                <div v-if="output.parsed.similarity_clusters && output.parsed.similarity_clusters.length > 0" class="content-section">
                                    <h6>Similarity Clusters ({{ output.parsed.similarity_clusters.length }})</h6>
                                    <div class="clusters-list">
                                        <div v-for="(cluster, i) in output.parsed.similarity_clusters" :key="i" class="cluster-item">
                                            <div class="cluster-header">
                                                <span class="cluster-id">{{ cluster.cluster_name || cluster.cluster_id }}</span>
                                            </div>
                                            <p v-if="cluster.central_theme" class="cluster-theme">{{ cluster.central_theme }}</p>
                                            <div v-if="cluster.similar_hypotheses && cluster.similar_hypotheses.length > 0" class="cluster-hypotheses">
                                                <strong>{{ cluster.similar_hypotheses.length }} Similar Hypotheses</strong>
                                                <ul>
                                                    <li v-for="(hyp, j) in cluster.similar_hypotheses.slice(0, 3)" :key="j">
                                                        {{ hyp.text }}
                                                        <span v-if="hyp.similarity_degree" class="similarity-badge">{{ hyp.similarity_degree }} similarity</span>
                                                    </li>
                                                </ul>
                                            </div>
                                            <p v-if="cluster.synthesis_potential" class="synthesis-note">
                                                <strong>Synthesis Potential:</strong> {{ cluster.synthesis_potential }}
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                <div v-if="output.parsed.diversity_assessment" class="content-section">
                                    <h6>Diversity Assessment</h6>
                                    <p>{{ output.parsed.diversity_assessment }}</p>
                                </div>
                            </div>
                        </Panel>

                        <!-- Fallback for unknown agents or unparsed data -->
                        <div v-else class="agent-content">
                            <pre class="raw-output">{{ output.content }}</pre>
                        </div>
                    </AccordionPanel>
                </Accordion>
            </div>

            <Message v-if="errorMessage" severity="error" :closable="true" @close="errorMessage = ''">
                {{ errorMessage }}
            </Message>
        </div>

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
import { ref, inject, onMounted, onUnmounted } from "vue";
import type { BeakerSessionComponentType } from '../session/BeakerSession.vue';
import Button from "primevue/button";
import Textarea from "primevue/textarea";
import ProgressBar from "primevue/progressbar";
import Message from "primevue/message";
import Divider from "primevue/divider";
import Accordion from "primevue/accordion";
import AccordionPanel from "primevue/accordionpanel";
import Panel from "primevue/panel";
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

const beakerSession = inject<BeakerSessionComponentType>("beakerSession");

const researchGoal = ref<string>("");
const isGenerating = ref<boolean>(false);
const progress = ref<number>(0);
const progressMessage = ref<string>("");
const errorMessage = ref<string>("");
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
                    // This is a phase marker - add it as a visual divider
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
                    console.log(`📍 Adding phase marker:`, phaseMarkerEntry);
                    agentOutputs.value.push(phaseMarkerEntry);
                    // Auto-scroll disabled - makes it hard to read incoming information
                    // scrollToLatest();
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
                                lines.shift(); // Remove first ```json or ```
                            }
                            if (lines[lines.length - 1].trim() === '```') {
                                lines.pop(); // Remove closing ```
                            }
                            cleanOutput = lines.join('\n').trim();
                        }

                        // Try to parse the JSON, handling concatenated/truncated outputs
                        try {
                            // Try normal parse first
                            parsed = JSON.parse(cleanOutput);
                        } catch (parseError) {
                            // If parse fails, try to extract first valid JSON object
                            // Find the first opening brace and try to find its matching closing brace
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
                        console.log(`✅ Parsed ${agent_name}:`, parsed);
                    } catch (e) {
                        // Failed to parse, use raw output
                        console.error(`❌ Failed to parse ${agent_name} output:`, e);
                        console.error("Raw output:", agent_output);
                        console.error("First 200 chars:", agent_output.substring(0, 200));
                        // Keep parsed as empty object so the fallback display shows raw content
                    }

                    const outputEntry = {
                        name: agent_name,
                        content: formattedContent,
                        parsed,
                        timestamp: Date.now(),
                        phase: phase,
                        iteration: iteration
                    };
                    console.log(`📦 Adding agent output:`, outputEntry);
                    agentOutputs.value.push(outputEntry);

                    // Auto-scroll disabled - makes it hard to read incoming information
                    // scrollToLatest();
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

const formatTimestamp = (timestamp: number): string => {
    return new Date(timestamp).toLocaleTimeString();
};

const truncate = (text: string, maxLength: number): string => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
};

const formatScoreName = (key: string): string => {
    // Convert snake_case to Title Case
    return key
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
};

const formatAgentName = (name: string): string => {
    // Convert agent name to readable format
    const nameMap: Record<string, string> = {
        'Supervisor': 'Research Supervisor',
        'HypothesisGenerator': 'Hypothesis Generator',
        'HypothesisReflector': 'Peer Reviewer',
        'HypothesisRanker': 'Hypothesis Ranker',
        'TournamentJudge': 'Tournament Judge',
        'MetaReviewer': 'Meta Reviewer',
        'HypothesisEvolver': 'Hypothesis Evolver',
        'ProximityAnalyzer': 'Proximity Analyzer',
        'EvolutionAgent': 'Evolution Agent'
    };
    return nameMap[name] || name;
};

const scrollToLatest = () => {
    // Auto-scroll to the latest agent output
    setTimeout(() => {
        const accordion = document.querySelector('.agent-accordion');
        if (accordion) {
            accordion.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    }, 100);
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

// Compact header when generating
.generating-header {
    position: sticky;
    top: 0;
    z-index: 100;
    background: var(--p-surface-0);
    border: 1px solid var(--p-surface-border);
    border-radius: 8px;
    padding: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);

    .header-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
    }

    .title-section {
        flex: 1;

        h3 {
            margin: 0 0 0.25rem 0;
            color: var(--p-text-color);
            font-size: 0.95rem;
            font-weight: 600;
        }

        .compact-goal {
            margin: 0;
            font-size: 0.8rem;
            color: var(--p-text-color-secondary);
            line-height: 1.3;
            max-height: 2.6em;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }
    }

    .cancel-button-compact {
        flex-shrink: 0;
    }

    .progress-bar {
        width: 100%;
        height: 6px;
    }

    .progress-message {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.75rem;
        color: var(--p-text-color-secondary);
    }
}

// Full input form
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

// Agent Activity Section
.agent-outputs {
    margin-top: 0.5rem;

    .section-title {
        margin: 0 0 0.75rem 0;
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--p-text-color);
    }

    .agent-accordion {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
}

.accordion-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    padding: 0.25rem 0;

    i {
        font-size: 1.1rem;
    }

    .agent-name {
        flex: 1;
        font-weight: 500;
        font-size: 0.875rem;
        color: var(--p-text-color);
    }

    .iteration-badge {
        padding: 0.15rem 0.5rem;
        background: var(--p-primary-color);
        color: white;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-left: auto;
        margin-right: 0.5rem;
    }

    .agent-time {
        font-size: 0.7rem;
        color: var(--p-text-color-secondary);
        font-family: monospace;
    }
}

.agent-content {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 0.75rem 0;

    h6 {
        margin: 0 0 0.5rem 0;
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--p-text-color);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    p {
        margin: 0;
        line-height: 1.5;
        font-size: 0.85rem;
        color: var(--p-text-color-secondary);
    }

    ul {
        margin: 0.25rem 0 0 0;
        padding-left: 1.25rem;

        li {
            margin: 0.25rem 0;
            line-height: 1.4;
            font-size: 0.85rem;
            color: var(--p-text-color-secondary);
        }
    }

    .content-section {
        padding-bottom: 0.5rem;

        & + .content-section {
            padding-top: 0.5rem;
            border-top: 1px solid var(--p-surface-border);
        }
    }
}

// Component-specific styles
.summary {
    font-weight: 400;
    margin-bottom: 1rem;
    color: var(--p-text-color);
    line-height: 1.6;
}

.key-areas {
    h6 {
        margin: 0 0 0.5rem 0;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--p-text-color-secondary);
    }

    ul {
        margin: 0;
        padding-left: 1.5rem;

        li {
            margin-bottom: 0.25rem;
            line-height: 1.5;
        }
    }
}

.workflow-section {
    h6 {
        margin: 0 0 0.75rem 0;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--p-text-color-secondary);
    }
}

.workflow-details {
    p {
        margin: 0.5rem 0;
        line-height: 1.5;

        strong {
            font-weight: 600;
            color: var(--p-text-color-secondary);
        }
    }
}

.list-section {
    margin-top: 0.5rem;
    font-size: 0.85rem;

    strong {
        color: var(--p-text-color);
        font-weight: 500;
    }
}

.hypothesis-list-compact {
    margin: 0.25rem 0 0 0;
    padding-left: 1.25rem;

    li {
        margin: 0.5rem 0;
        line-height: 1.4;
        font-size: 0.85rem;
        color: var(--p-text-color-secondary);
    }
}

// Agent Panel styles
.agent-panel {
    margin-bottom: 1rem;

    .content-section {
        margin-bottom: 1rem;

        &:last-child {
            margin-bottom: 0;
        }
    }
}

// Peer Reviewer styles
.review-hypothesis {
    padding: 0.75rem;
    background: var(--p-surface-50);
    border-left: 3px solid var(--p-primary-color);
    border-radius: 4px;
    margin-bottom: 1rem;

    .hypothesis-text {
        font-style: italic;
        color: var(--p-text-color);
        font-weight: 400;
        font-size: 0.9rem;
        line-height: 1.5;
        margin: 0;
    }
}

.overall-score {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: var(--p-surface-50);
    border-radius: 4px;

    .score-label {
        font-weight: 500;
        font-size: 0.85rem;
        color: var(--p-text-color);
    }

    .score-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--p-primary-color);
    }
}

.score-grid {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.score-item {
    display: grid;
    grid-template-columns: 120px 1fr 50px;
    align-items: center;
    gap: 0.5rem;

    .score-name {
        font-size: 0.75rem;
        color: var(--p-text-color-secondary);
    }

    .score-bar {
        height: 6px;
    }

    .score-num {
        text-align: right;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--p-text-color);
    }
}

// Ranker styles
.ranked-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.ranked-item {
    display: flex;
    gap: 0.75rem;
    padding: 0.5rem;
    background: var(--p-surface-50);
    border-radius: 4px;

    .rank-badge {
        flex-shrink: 0;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--p-primary-color);
        color: white;
        font-weight: 600;
        font-size: 0.75rem;
        border-radius: 4px;
    }

    .rank-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;

        .rank-hypothesis {
            font-weight: 400;
            font-size: 0.85rem;
            color: var(--p-text-color);
            margin: 0;
        }

        .rank-explanation {
            font-size: 0.75rem;
            color: var(--p-text-color-secondary);
            font-style: italic;
            margin: 0;
        }

        .rank-score {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--p-primary-color);
        }
    }
}

// Fallback raw output
.raw-output {
    margin: 0;
    padding: 0.75rem;
    background-color: #1e1e1e;
    border-radius: 4px;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
    font-size: 0.75rem;
    line-height: 1.5;
    overflow-x: auto;
    white-space: pre-wrap;
    color: #d4d4d4;
    max-height: 300px;
    overflow-y: auto;
}

// Results section
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

.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 3rem 1rem;
    text-align: center;
    color: var(--p-text-color-secondary);
}

// Tournament Judge styles
.tournament-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.tournament-matchup {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 1rem;
    align-items: center;
}

.hypothesis-box {
    padding: 0.75rem;
    background: var(--p-surface-50);
    border: 1px solid var(--p-surface-200);
    border-radius: 6px;

    .hypothesis-label {
        font-weight: 600;
        font-size: 0.75rem;
        color: var(--p-text-color-secondary);
        text-transform: uppercase;
        margin-bottom: 0.5rem;
        letter-spacing: 0.5px;
    }

    p {
        margin: 0;
        font-size: 0.85rem;
        line-height: 1.4;
    }
}

.vs-divider {
    font-weight: 700;
    font-size: 0.9rem;
    color: var(--p-text-color-secondary);
    padding: 0 0.5rem;
}

.winner-section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.75rem;
    background: var(--p-highlight-bg);
    border-left: 3px solid var(--p-primary-color);
    border-radius: 4px;
}

.winner-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--p-primary-color);

    i {
        color: #ff3b30;
    }
}

.decision-summary {
    margin: 0;
    font-size: 0.85rem;
    line-height: 1.5;
    color: var(--p-text-color);
}

.judgment-panel {
    margin-top: 0.5rem;
}

.comparison-grid {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.comparison-item {
    h6 {
        margin: 0 0 0.25rem 0;
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--p-text-color-secondary);
        text-transform: capitalize;
    }

    p {
        margin: 0;
        font-size: 0.85rem;
        line-height: 1.5;
        color: var(--p-text-color);
    }
}

// MetaReviewer styles
.themes-list, .recommendations-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.theme-item {
    padding: 0.75rem;
    background: var(--p-surface-50);
    border-left: 3px solid var(--p-primary-color);
    border-radius: 4px;

    .theme-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;

        strong {
            font-size: 0.9rem;
            color: var(--p-text-color);
        }
    }

    .theme-frequency {
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
        background: var(--p-primary-color);
        color: white;
        border-radius: 12px;
    }

    p {
        margin: 0;
        font-size: 0.85rem;
        line-height: 1.5;
        color: var(--p-text-color-secondary);
    }
}

.recommendation-item {
    padding: 0.75rem;
    background: var(--p-surface-50);
    border-left: 3px solid var(--p-highlight-text-color);
    border-radius: 4px;

    .rec-header {
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
        color: var(--p-text-color);
    }

    p {
        margin: 0.5rem 0;
        font-size: 0.85rem;
        line-height: 1.5;

        strong {
            font-weight: 600;
            color: var(--p-text-color-secondary);
        }
    }

    .rec-justification {
        font-style: italic;
        color: var(--p-text-color-secondary);
    }
}

// HypothesisEvolver styles
.evolution-comparison {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 1rem;
    align-items: start;
    margin-bottom: 1.5rem;
}

.evolution-box {
    padding: 0.75rem;
    border-radius: 6px;
    border: 2px solid;

    &.original {
        border-color: var(--p-surface-300);
        background: var(--p-surface-50);
    }

    &.refined {
        border-color: var(--p-primary-color);
        background: var(--p-highlight-bg);
    }

    .evolution-label {
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
        color: var(--p-text-color-secondary);
    }

    p {
        margin: 0;
        font-size: 0.85rem;
        line-height: 1.5;
    }
}

.evolution-arrow {
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--p-primary-color);
    font-size: 1.5rem;
}

.refinements-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.refinement-item {
    padding: 0.75rem;
    background: var(--p-surface-50);
    border-radius: 4px;
    border-left: 3px solid var(--p-surface-300);

    .refinement-aspect {
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
        color: var(--p-primary-color);
        text-transform: capitalize;
    }

    p {
        margin: 0.5rem 0;
        font-size: 0.85rem;
        line-height: 1.5;

        strong {
            font-weight: 600;
            color: var(--p-text-color-secondary);
        }
    }

    .refinement-just {
        font-style: italic;
        color: var(--p-text-color-secondary);
    }
}

// ProximityAnalyzer styles
.clusters-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.cluster-item {
    padding: 0.75rem;
    background: var(--p-surface-50);
    border: 1px solid var(--p-surface-200);
    border-radius: 6px;

    .cluster-header {
        margin-bottom: 0.75rem;

        .cluster-id {
            font-weight: 600;
            font-size: 0.9rem;
            color: var(--p-primary-color);
        }
    }

    .cluster-theme {
        margin: 0 0 0.75rem 0;
        font-size: 0.85rem;
        line-height: 1.5;
        color: var(--p-text-color);
        font-style: italic;
    }

    .cluster-hypotheses {
        margin: 0.75rem 0;

        strong {
            display: block;
            margin-bottom: 0.5rem;
            font-size: 0.8rem;
            color: var(--p-text-color-secondary);
        }

        ul {
            margin: 0;
            padding-left: 1.5rem;

            li {
                margin-bottom: 0.5rem;
                font-size: 0.85rem;
                line-height: 1.4;

                .similarity-badge {
                    display: inline-block;
                    margin-left: 0.5rem;
                    padding: 0.15rem 0.4rem;
                    font-size: 0.7rem;
                    background: var(--p-primary-color);
                    color: white;
                    border-radius: 10px;
                }
            }
        }
    }

    .synthesis-note {
        margin: 0.75rem 0 0 0;
        padding-top: 0.75rem;
        border-top: 1px solid var(--p-surface-200);
        font-size: 0.85rem;
        line-height: 1.5;

        strong {
            color: var(--p-text-color-secondary);
        }
    }
}

// Phase Marker styles
.phase-marker-header {
    background: linear-gradient(90deg, var(--p-primary-color) 0%, transparent 100%);
    padding: 0.5rem 0.75rem !important;
    border-radius: 6px;

    .agent-name {
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        color: var(--p-primary-color) !important;
    }
}

.phase-marker-content {
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    background: linear-gradient(135deg, var(--p-highlight-bg) 0%, var(--p-surface-0) 100%);
    border-top: 3px solid var(--p-primary-color);
    border-bottom: 3px solid var(--p-primary-color);
}

.phase-marker-badge {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1.5rem;
    background: var(--p-primary-color);
    color: white;
    border-radius: 24px;
    font-weight: 700;
    font-size: 1.1rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

    i {
        font-size: 1.2rem;
    }
}

.phase-marker-description {
    margin: 0;
    text-align: center;
    font-size: 0.9rem;
    line-height: 1.5;
    color: var(--p-text-color);
    font-style: italic;
    max-width: 600px;
}
</style>
