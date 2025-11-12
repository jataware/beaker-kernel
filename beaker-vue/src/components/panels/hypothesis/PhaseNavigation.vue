<template>
    <div v-if="phases.length > 1" class="phase-navigation">
        <Button
            v-for="phase in phases"
            :key="phase.id"
            :label="phase.name"
            :icon="phase.icon"
            size="small"
            :severity="selectedPhaseId === phase.id ? 'primary' : 'secondary'"
            text
            @click="selectPhase(phase.id)"
            class="phase-nav-button"
            :style="{ '--phase-color': phase.color }"
        />
    </div>
</template>

<script setup lang="ts">
import Button from 'primevue/button';

interface PhaseInfo {
    id: string;
    name: string;
    color: string;
    icon: string;
}

defineProps<{
    phases: PhaseInfo[];
    selectedPhaseId?: string | null;
}>();

const emit = defineEmits<{
    'select-phase': [phaseId: string];
}>();

const selectPhase = (phaseId: string) => {
    emit('select-phase', phaseId);
};
</script>

<style lang="scss" scoped>
.phase-navigation {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    padding: 0.5rem;
    background: var(--p-surface-50);
    border-radius: 6px;
    margin-bottom: 0.75rem;

    .phase-nav-button {
        padding: 0.375rem 0.75rem;
        font-size: 0.8rem;
        transition: all 0.2s;

        &:deep(.p-button.p-button-text) {
            &:hover {
                background: var(--phase-color, var(--p-primary-color));
                opacity: 0.1;
            }
        }

        &:deep(.p-button.p-button-text.p-button-primary) {
            background: var(--phase-color, var(--p-primary-color));
            color: white;

            &:hover {
                opacity: 0.9;
            }
        }
    }
}
</style>
