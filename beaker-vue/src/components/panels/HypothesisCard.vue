<template>
    <Card class="hypothesis-card">
        <template #header>
            <div class="hypothesis-header">
                <div class="rank-badge">
                    <Badge :value="`#${rank}`" severity="info" />
                </div>
                <div class="scores">
                    <div class="score-item" title="Composite Score (0-1)">
                        <i class="pi pi-star-fill"></i>
                        <span>{{ hypothesis.score.toFixed(3) }}</span>
                    </div>
                    <div class="score-item" title="Elo Rating">
                        <i class="pi pi-trophy"></i>
                        <span>{{ hypothesis.elo_rating }}</span>
                    </div>
                    <div class="score-item" title="Tournament Record">
                        <i class="pi pi-chart-bar"></i>
                        <span>{{ hypothesis.win_count }}W / {{ hypothesis.loss_count }}L</span>
                    </div>
                </div>
            </div>
        </template>

        <template #content>
            <div class="hypothesis-content">
                <p class="hypothesis-text">{{ hypothesis.text }}</p>

                <div v-if="hasEvolution" class="evolution-indicator">
                    <Tag severity="success" :value="`Evolved ${getEvolutionCount()}x`" icon="pi pi-sync" />
                    <span class="evolution-summary">{{ getEvolutionSummary() }}</span>
                </div>

                <div v-if="hypothesis.similarity_cluster_id" class="cluster-indicator">
                    <Tag severity="info" :value="`Cluster: ${hypothesis.similarity_cluster_id}`" icon="pi pi-sitemap" />
                </div>

                <Accordion v-if="hypothesis.reviews && hypothesis.reviews.length > 0" class="reviews-accordion">
                    <AccordionTab :header="`Reviews (${hypothesis.reviews.length})`">
                        <div class="reviews-list">
                            <div v-for="(review, idx) in hypothesis.reviews" :key="idx" class="review-item">
                                <div class="review-header">
                                    <strong>Review {{ idx + 1 }}</strong>
                                    <span v-if="review.scores" class="review-summary">{{ getReviewSummary(review) }}</span>
                                </div>

                                <!-- Show full review content -->
                                <div v-if="review.review_summary || review.summary" class="review-summary-text">
                                    <h6>Summary</h6>
                                    <p>{{ review.review_summary || review.summary }}</p>
                                </div>

                                <div v-if="review.feedback || review.constructive_feedback" class="review-feedback">
                                    <h6>Feedback</h6>
                                    <p>{{ review.feedback || review.constructive_feedback }}</p>
                                </div>

                                <!-- Strengths and Weaknesses -->
                                <div v-if="review.strengths || review.weaknesses" class="review-strengths-weaknesses">
                                    <div v-if="review.strengths" class="strengths-section">
                                        <h6>Strengths</h6>
                                        <p>{{ review.strengths }}</p>
                                    </div>
                                    <div v-if="review.weaknesses" class="weaknesses-section">
                                        <h6>Areas for Improvement</h6>
                                        <p>{{ review.weaknesses }}</p>
                                    </div>
                                </div>

                                <!-- Detailed Scores -->
                                <div v-if="review.scores && Object.keys(review.scores).length > 0" class="review-scores-detailed">
                                    <h6>Detailed Scores</h6>
                                    <div class="score-grid">
                                        <div v-for="(value, criterion) in review.scores" :key="String(criterion)" class="score-row">
                                            <span class="score-label">{{ formatCriterion(String(criterion)) }}</span>
                                            <div class="score-bar-container">
                                                <div class="score-bar" :style="{ width: (value / 5 * 100) + '%' }"></div>
                                            </div>
                                            <span class="score-value">{{ value }}/5</span>
                                        </div>
                                    </div>
                                </div>

                                <!-- Overall Score -->
                                <div v-if="review.overall_score !== undefined" class="overall-score-badge">
                                    <i class="pi pi-star-fill"></i>
                                    <span>Overall: {{ (review.overall_score * 100).toFixed(0) }}%</span>
                                </div>
                            </div>
                        </div>
                    </AccordionTab>

                    <AccordionTab v-if="hasEvolution" header="Evolution History">
                        <div class="evolution-history">
                            <div v-for="(entry, idx) in getFilteredEvolution()" :key="idx" class="evolution-step">
                                <div class="step-header">
                                    <span class="step-number">Step {{ idx + 1 }}</span>
                                </div>
                                <p class="step-description">{{ entry }}</p>
                            </div>
                            <div v-if="getFilteredEvolution().length === 0" class="no-evolution">
                                <p>Evolution data not available</p>
                            </div>
                        </div>
                    </AccordionTab>
                </Accordion>
            </div>
        </template>

        <template #footer>
            <div class="hypothesis-actions">
                <Button
                    label="Copy"
                    icon="pi pi-copy"
                    size="small"
                    text
                    @click="copyHypothesis"
                />
                <Button
                    label="Export"
                    icon="pi pi-download"
                    size="small"
                    text
                    @click="exportHypothesis"
                />
            </div>
        </template>
    </Card>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import Card from "primevue/card";
import Badge from "primevue/badge";
import Tag from "primevue/tag";
import Button from "primevue/button";
import Accordion from "primevue/accordion";
import AccordionTab from "primevue/accordiontab";

interface Review {
    scores: { [key: string]: number };
    feedback?: string;
}

interface Hypothesis {
    text: string;
    score: number;
    elo_rating: number;
    reviews: Review[];
    similarity_cluster_id?: string;
    evolution_history: string[];
    win_count: number;
    loss_count: number;
}

const props = defineProps<{
    hypothesis: Hypothesis;
    rank: number;
}>();

const formatCriterion = (criterion: string): string => {
    return criterion
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
};

const getReviewSummary = (review: Review): string => {
    if (!review.scores) return '';

    const scores = Object.values(review.scores);
    if (scores.length === 0) return '';

    const avg = scores.reduce((sum, val) => sum + val, 0) / scores.length;
    const avgRounded = avg.toFixed(1);

    if (avg >= 4.5) return `Excellent (${avgRounded}/5)`;
    if (avg >= 4.0) return `Very Good (${avgRounded}/5)`;
    if (avg >= 3.5) return `Good (${avgRounded}/5)`;
    if (avg >= 3.0) return `Fair (${avgRounded}/5)`;
    if (avg >= 2.0) return `Needs Work (${avgRounded}/5)`;
    return `Poor (${avgRounded}/5)`;
};

const hasEvolution = computed(() => {
    return props.hypothesis.evolution_history &&
           props.hypothesis.evolution_history.length > 0;
});

const getEvolutionCount = (): number => {
    if (!props.hypothesis.evolution_history) return 0;
    return props.hypothesis.evolution_history.length;
};

const getFilteredEvolution = (): string[] => {
    if (!props.hypothesis.evolution_history) return [];

    // Filter out empty strings and duplicates
    const unique = new Set<string>();
    return props.hypothesis.evolution_history.filter(entry => {
        if (!entry || entry.trim() === '') return false;
        if (unique.has(entry)) return false;
        unique.add(entry);
        return true;
    });
};

const getEvolutionSummary = (): string => {
    const filtered = getFilteredEvolution();
    if (filtered.length === 0) return 'No evolution steps recorded';
    if (filtered.length === 1) return 'Refined once based on feedback';
    return `Refined ${filtered.length} times through iterative improvement`;
};

const copyHypothesis = async () => {
    try {
        await navigator.clipboard.writeText(props.hypothesis.text);
        // You could add a toast notification here
    } catch (error) {
        console.error("Failed to copy hypothesis:", error);
    }
};

const exportHypothesis = () => {
    const data = {
        rank: props.rank,
        text: props.hypothesis.text,
        score: props.hypothesis.score,
        elo_rating: props.hypothesis.elo_rating,
        win_count: props.hypothesis.win_count,
        loss_count: props.hypothesis.loss_count,
        reviews: props.hypothesis.reviews,
        evolution_history: props.hypothesis.evolution_history,
        cluster_id: props.hypothesis.similarity_cluster_id,
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hypothesis_${props.rank}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
};
</script>

<style lang="scss" scoped>
.hypothesis-card {
    border-left: 4px solid var(--p-primary-color);
    transition: transform 0.2s, box-shadow 0.2s;

    &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
}

.hypothesis-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: var(--p-surface-100);
    border-bottom: 1px solid var(--p-surface-border);

    .rank-badge {
        font-size: 1.2rem;
    }

    .scores {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;

        .score-item {
            display: flex;
            align-items: center;
            gap: 0.25rem;
            font-size: 0.875rem;
            color: var(--p-text-color-secondary);

            i {
                color: var(--p-primary-color);
            }
        }
    }
}

.hypothesis-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;

    .hypothesis-text {
        font-size: 1rem;
        line-height: 1.6;
        margin: 0;
    }

    .evolution-indicator {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.5rem;
        background: var(--p-surface-50);
        border-radius: var(--p-border-radius);

        .evolution-summary {
            font-size: 0.875rem;
            color: var(--p-text-color-secondary);
        }
    }

    .cluster-indicator {
        display: flex;
        gap: 0.5rem;
    }
}

.reviews-accordion {
    margin-top: 1rem;

    .reviews-list {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }

    .review-item {
        padding: 1rem;
        background: var(--p-surface-50);
        border-radius: var(--p-border-radius);
        margin-bottom: 0.75rem;

        .review-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--p-surface-border);

            strong {
                color: var(--p-text-color);
                font-size: 1rem;
            }

            .review-summary {
                font-size: 0.875rem;
                color: var(--p-primary-color);
                font-weight: 600;
            }
        }

        h6 {
            margin: 0 0 0.5rem 0;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--p-text-color-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .review-summary-text {
            margin-bottom: 1rem;

            p {
                margin: 0;
                line-height: 1.6;
                color: var(--p-text-color);
                font-size: 0.9rem;
            }
        }

        .review-feedback {
            margin-bottom: 1rem;

            p {
                margin: 0;
                line-height: 1.6;
                color: var(--p-text-color);
                font-size: 0.9rem;
            }
        }

        .review-strengths-weaknesses {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1rem;

            @media (max-width: 768px) {
                grid-template-columns: 1fr;
            }

            .strengths-section, .weaknesses-section {
                padding: 0.75rem;
                border-radius: 4px;
            }

            .strengths-section {
                background: rgba(52, 199, 89, 0.1);
                border-left: 3px solid #34c759;

                h6 {
                    color: #34c759;
                }
            }

            .weaknesses-section {
                background: rgba(255, 149, 0, 0.1);
                border-left: 3px solid #ff9500;

                h6 {
                    color: #ff9500;
                }
            }

            p {
                margin: 0;
                line-height: 1.5;
                font-size: 0.875rem;
                color: var(--p-text-color);
            }
        }

        .review-scores-detailed {
            margin-bottom: 1rem;

            .score-grid {
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
            }

            .score-row {
                display: grid;
                grid-template-columns: 140px 1fr 60px;
                align-items: center;
                gap: 0.75rem;

                .score-label {
                    font-size: 0.875rem;
                    color: var(--p-text-color);
                    font-weight: 500;
                }

                .score-bar-container {
                    height: 8px;
                    background: var(--p-surface-100);
                    border-radius: 4px;
                    overflow: hidden;

                    .score-bar {
                        height: 100%;
                        background: linear-gradient(90deg, var(--p-primary-color), var(--p-primary-600));
                        border-radius: 4px;
                        transition: width 0.3s ease;
                    }
                }

                .score-value {
                    text-align: right;
                    font-size: 0.875rem;
                    font-weight: 600;
                    color: var(--p-text-color);
                }
            }
        }

        .overall-score-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: var(--p-primary-color);
            color: white;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;

            i {
                color: #ffd700;
            }
        }

        .review-scores-compact {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.5rem;

            .score-badge {
                font-size: 0.75rem;
                padding: 0.25rem 0.5rem;
                background: var(--p-surface-100);
                border-radius: var(--p-border-radius);
                color: var(--p-text-color-secondary);
            }
        }
    }
}

.evolution-history {
    display: flex;
    flex-direction: column;
    gap: 1rem;

    .evolution-step {
        padding: 0.75rem;
        background: var(--p-surface-50);
        border-radius: var(--p-border-radius);
        border-left: 3px solid var(--p-primary-color);

        .step-header {
            margin-bottom: 0.5rem;

            .step-number {
                font-size: 0.875rem;
                font-weight: 600;
                color: var(--p-primary-color);
            }
        }

        .step-description {
            margin: 0;
            line-height: 1.6;
            color: var(--p-text-color);
        }
    }

    .no-evolution {
        padding: 1rem;
        text-align: center;
        color: var(--p-text-color-secondary);
        font-style: italic;

        p {
            margin: 0;
        }
    }
}

.hypothesis-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
}
</style>
