<template>
    <Fieldset legend="Available Resources" v-if="fileResources.length > 0">
        <p>
            These resources are available to the agent and will be loaded on demand when the skill is active.
        </p>
        <div class="skill-resource-link-list">
            <div
                class="skill-resource-link"
                v-for="resource in fileResources"
                :key="resource.resource_id"
                @click="emit('open-resource', resource.resource_id)"
            >
                <i class="pi pi-file"></i>
                <span class="skill-resource-link-path">{{ resource.relative_path }}</span>
                <i class="pi pi-chevron-right skill-resource-link-arrow"></i>
            </div>
        </div>
    </Fieldset>

    <Fieldset legend="Code Examples" v-if="exampleResources.length > 0">
        <p>
            Code examples demonstrating usage patterns for this skill.
        </p>
        <div class="skill-resource-link-list">
            <div
                class="skill-resource-link"
                v-for="example in exampleResources"
                :key="example.resource_id"
                @click="emit('open-resource', example.resource_id)"
            >
                <i class="pi pi-code"></i>
                <div class="skill-resource-link-info">
                    <span class="skill-resource-link-path">{{ example.filename }}</span>
                    <span class="skill-resource-link-title">{{ example.title }}</span>
                </div>
                <i class="pi pi-chevron-right skill-resource-link-arrow"></i>
            </div>
        </div>
    </Fieldset>
</template>


<script setup lang="ts">
// The clickable Available Resources / Code Examples lists shared by the skill
// viewer and editor; clicking an item asks the parent to open that resource
// (focused in the right-side resource panel).

import Fieldset from 'primevue/fieldset';
import type { SkillFileResource, SkillExampleResource } from '../../util/integration';

defineProps<{
    fileResources: SkillFileResource[],
    exampleResources: SkillExampleResource[],
}>();

const emit = defineEmits<{
    (e: 'open-resource', resourceId: string): void,
}>();

</script>


<style lang="scss">
.skill-resource-link-list {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.skill-resource-link {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.5rem;
    border-radius: 4px;
    font-size: 0.9rem;
    cursor: pointer;

    &:hover {
        background-color: var(--p-surface-100);
    }

    .skill-resource-link-arrow {
        margin-left: auto;
        opacity: 0;
        transition: opacity 150ms linear;
    }

    &:hover .skill-resource-link-arrow {
        opacity: 1;
    }
}

.skill-resource-link-path {
    font-family: monospace;
}

.skill-resource-link-info {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
}

.skill-resource-link-title {
    font-size: 0.85rem;
    color: var(--p-text-muted-color);
}
</style>
