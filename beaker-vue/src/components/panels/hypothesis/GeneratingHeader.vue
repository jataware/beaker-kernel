<template>
    <div class="generating-header">
        <div class="header-row">
            <div class="title-section">
                <h3>Generating Hypotheses</h3>
                <p class="compact-goal">{{ researchGoal }}</p>
            </div>
            <Button
                @click="$emit('cancel')"
                label="Cancel"
                icon="pi pi-times"
                severity="danger"
                text
                class="cancel-button"
            />
        </div>
        <ProgressBar :value="progress" :showValue="false" class="progress-bar" />
        <div class="progress-message">
            <i class="pi pi-spin pi-spinner"></i>
            {{ progressMessage }}
        </div>
    </div>
</template>

<script setup lang="ts">
import Button from 'primevue/button';
import ProgressBar from 'primevue/progressbar';

defineProps<{
    researchGoal: string;
    progress: number;
    progressMessage: string;
}>();

defineEmits<{
    'cancel': [];
}>();
</script>

<style lang="scss" scoped>
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

    .cancel-button {
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
</style>
