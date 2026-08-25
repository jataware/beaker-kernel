<template>
    <div class="skill-integration-viewer">
        <div class="skill-viewer-content">
            <Fieldset legend="Name">
                <InputText
                    :model-value="selectedIntegration?.name"
                    disabled
                />
            </Fieldset>

            <Fieldset legend="Description">
                <div class="skill-description" v-html="renderedDescription"></div>
            </Fieldset>

            <Fieldset legend="Metadata" v-if="metadata">
                <div class="skill-metadata-grid">
                    <div class="skill-metadata-row" v-if="metadata.license">
                        <span class="skill-metadata-label">License</span>
                        <span class="skill-metadata-value">{{ metadata.license }}</span>
                    </div>
                    <div class="skill-metadata-row" v-if="metadata.compatibility">
                        <span class="skill-metadata-label">Compatibility</span>
                        <span class="skill-metadata-value">{{ metadata.compatibility }}</span>
                    </div>
                    <div class="skill-metadata-row" v-if="metadata.allowed_tools">
                        <span class="skill-metadata-label">Allowed Tools</span>
                        <span class="skill-metadata-value" style="font-family: monospace;">{{ metadata.allowed_tools }}</span>
                    </div>
                    <template v-for="(value, key) in (metadata.skill_metadata ?? {})" :key="key">
                        <div class="skill-metadata-row">
                            <span class="skill-metadata-label">{{ key }}</span>
                            <span class="skill-metadata-value">{{ value }}</span>
                        </div>
                    </template>
                </div>
                <div v-if="!hasMetadata" class="skill-no-metadata">
                    <i>No metadata available for this skill.</i>
                </div>
            </Fieldset>

            <Fieldset legend="Instructions (SKILL.md)" v-if="renderedInstructions">
                <ClampedMarkdown :html="renderedInstructions" @link-click="onInstructionsLinkClick" />
            </Fieldset>

            <SkillResourceLinks
                :file-resources="fileResources"
                :example-resources="exampleResources"
                @open-resource="(resourceId) => emit('open-resource', resourceId)"
            />
        </div>
    </div>
</template>


<script setup lang="ts">

import { computed } from 'vue';
import {
    type Integration,
    type IntegrationInterfaceState,
    type SkillMetadataResource,
    type SkillInstructionsResource,
    type SkillFileResource,
    type SkillExampleResource,
    filterByResourceType,
    resourceFromLinkClick,
} from '../../util/integration';

import Fieldset from 'primevue/fieldset';
import InputText from 'primevue/inputtext';
import ClampedMarkdown from '../misc/ClampedMarkdown.vue';
import SkillResourceLinks from './SkillResourceLinks.vue';

import { renderMarkdown } from '../../util/markdown';

const props = defineProps<{
    fetchResources: () => Promise<void>,
}>();

const emit = defineEmits<{
    (e: 'open-resource', resourceId: string): void,
}>();

const model = defineModel<IntegrationInterfaceState>();

const selectedIntegration = computed<Integration>(() =>
    model.value.integrations[model.value.selected]);

const renderedDescription = computed<string>(() =>
    renderMarkdown(selectedIntegration.value?.description));

const renderedInstructions = computed<string>(() => {
    const instructions = Object.values(filterByResourceType<SkillInstructionsResource>(
        selectedIntegration.value?.resources, "skill_instructions"))[0];
    return renderMarkdown(instructions?.content);
});

const onInstructionsLinkClick = (event: MouseEvent) => {
    const resource = resourceFromLinkClick(event, selectedIntegration.value);
    if (resource) {
        emit('open-resource', resource.resource_id);
    }
};

const metadata = computed<SkillMetadataResource | undefined>(() => {
    const resources = filterByResourceType<SkillMetadataResource>(
        selectedIntegration.value?.resources, "skill_metadata");
    return Object.values(resources)[0];
});

const hasMetadata = computed<boolean>(() => {
    if (!metadata.value) return false;
    return !!(metadata.value.license
        || metadata.value.compatibility
        || metadata.value.allowed_tools
        || Object.keys(metadata.value.skill_metadata ?? {}).length > 0);
});

const fileResources = computed<SkillFileResource[]>(() => {
    const resources = filterByResourceType<SkillFileResource>(
        selectedIntegration.value?.resources, "skill_file");
    return Object.values(resources);
});

const exampleResources = computed<SkillExampleResource[]>(() => {
    const resources = filterByResourceType<SkillExampleResource>(
        selectedIntegration.value?.resources, "skill_example");
    return Object.values(resources);
});

</script>

<style lang="scss">
.skill-integration-viewer {
    display: flex;
    flex-direction: column;
    height: 100%;

    .skill-viewer-content {
        flex: 1 1 auto;
        min-height: 0;
        overflow: auto;
        display: flex;
        flex-direction: column;
    }
}

.skill-metadata-grid {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.skill-metadata-row {
    display: flex;
    flex-direction: row;
    gap: 1rem;
    align-items: baseline;

    .skill-metadata-label {
        font-weight: 600;
        min-width: 8rem;
        flex-shrink: 0;
    }

    .skill-metadata-value {
        flex: 1;
    }
}

.skill-no-metadata {
    color: var(--p-text-muted-color);
}
</style>
