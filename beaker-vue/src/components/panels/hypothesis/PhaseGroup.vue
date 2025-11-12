<template>
    <div class="phase-group" :data-phase-id="phase.id">
        <div
            class="phase-header"
            :style="{ '--phase-color': phase.color }"
            @click="toggleExpanded"
        >
            <i :class="['pi', phase.icon]" class="phase-icon"></i>
            <span class="phase-name">{{ phase.name }}</span>
            <span class="phase-count">{{ agentCount }}</span>
            <span class="phase-summary">{{ phase.summary }}</span>
            <i :class="isExpanded ? 'pi pi-chevron-up' : 'pi pi-chevron-down'" class="expand-icon"></i>
        </div>

        <div v-if="isExpanded" class="phase-content">
            <slot></slot>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface PhaseInfo {
    id: string;
    name: string;
    color: string;
    icon: string;
    summary: string;
}

const props = defineProps<{
    phase: PhaseInfo;
    agentCount: number;
    defaultExpanded?: boolean;
}>();

const emit = defineEmits<{
    'toggle': [phaseId: string, expanded: boolean];
}>();

const isExpanded = ref(props.defaultExpanded ?? false);

const toggleExpanded = () => {
    isExpanded.value = !isExpanded.value;
    emit('toggle', props.phase.id, isExpanded.value);
};

// Allow parent to control expansion
defineExpose({
    expand: () => { isExpanded.value = true; },
    collapse: () => { isExpanded.value = false; },
    toggle: toggleExpanded
});
</script>

<style lang="scss" scoped>
.phase-group {
    border: 1px solid var(--p-surface-border);
    border-radius: 6px;
    overflow: hidden;
    background: var(--p-surface-0);
}

.phase-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0.75rem;
    background: linear-gradient(90deg, var(--phase-color, var(--p-primary-color)) 0%, transparent 100%);
    opacity: 0.95;
    border-left: 4px solid var(--phase-color, var(--p-primary-color));
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
        opacity: 1;
        background: linear-gradient(90deg, var(--phase-color, var(--p-primary-color)) 0%, var(--p-surface-50) 100%);
    }

    .phase-icon {
        font-size: 1rem;
        color: var(--phase-color, var(--p-primary-color));
        filter: brightness(0.8);
    }

    .phase-name {
        font-weight: 600;
        font-size: 0.9rem;
        color: var(--p-text-color);
    }

    .phase-count {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 22px;
        height: 22px;
        padding: 0 0.4rem;
        background: var(--phase-color, var(--p-primary-color));
        color: white;
        border-radius: 11px;
        font-size: 0.7rem;
        font-weight: 600;
    }

    .phase-summary {
        flex: 1;
        font-size: 0.75rem;
        color: var(--p-text-color-secondary);
        opacity: 0.9;
    }

    .expand-icon {
        font-size: 0.8rem;
        color: var(--p-text-color-secondary);
    }
}

.phase-content {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.5rem;
}
</style>
