<template>
    <div v-if="output.parsed" class="proximity-agent">
        <!-- Compact view: cluster count and toggle on one line -->
        <div class="compact-row">
            <div v-if="output.parsed.similarity_clusters && output.parsed.similarity_clusters.length > 0" class="clusters-compact">
                <i class="pi pi-sitemap"></i>
                <span>{{ output.parsed.similarity_clusters.length }} Similarity Clusters</span>
            </div>

            <div class="expand-toggle" @click="expanded = !expanded">
                <span>{{ expanded ? 'Hide' : 'Show' }} Details</span>
                <i :class="expanded ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"></i>
            </div>
        </div>

        <!-- Expanded view: all cluster details -->
        <div v-if="expanded" class="expanded-content">
            <div v-if="output.parsed.similarity_clusters && output.parsed.similarity_clusters.length > 0" class="clusters-full">
                <strong>Similarity Clusters:</strong>
                <div class="cluster-list">
                    <div v-for="(cluster, i) in output.parsed.similarity_clusters" :key="i" class="cluster-item">
                        <span class="cluster-name">{{ cluster.cluster_name || `Cluster ${i + 1}` }}</span>
                        <span v-if="cluster.central_theme" class="cluster-theme">{{ cluster.central_theme }}</span>
                        <span v-if="cluster.similar_hypotheses" class="cluster-count">
                            {{ cluster.similar_hypotheses.length }} hypotheses
                        </span>
                    </div>
                </div>
            </div>

            <div v-if="output.parsed.diversity_assessment" class="diversity">
                <strong>Diversity Assessment:</strong>
                <p>{{ output.parsed.diversity_assessment }}</p>
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
</script>

<style lang="scss" scoped>
.proximity-agent {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    font-size: 0.85rem;

    .compact-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .clusters-compact {
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.375rem 0.5rem;
        background: var(--p-surface-100);
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--p-text-color);

        i {
            font-size: 0.8rem;
            color: var(--p-primary-color);
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

    .clusters-full {
        .cluster-list {
            display: flex;
            flex-direction: column;
            gap: 0.375rem;
            margin-top: 0.25rem;
        }

        .cluster-item {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            padding: 0.375rem 0.5rem;
            background: var(--p-surface-100);
            border-radius: 4px;
            border-left: 3px solid var(--p-primary-color);

            .cluster-name {
                font-weight: 600;
                font-size: 0.8rem;
                color: var(--p-primary-color);
            }

            .cluster-theme {
                font-size: 0.75rem;
                font-style: italic;
                color: var(--p-text-color);
                line-height: 1.3;
            }

            .cluster-count {
                font-size: 0.7rem;
                color: var(--p-text-color-secondary);
            }
        }
    }
}
</style>
