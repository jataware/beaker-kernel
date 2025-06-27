<template>
    <div class="integrations-panel">
        <div class="integration-header">
            <InputGroup>
                <InputGroupAddon>
                    <i class="pi pi-search"></i>
                </InputGroupAddon>
                <InputText placeholder="Search Integrations..." v-model="searchText">
                </InputText>
                <Button
                    v-if="searchText !== undefined && searchText !== ''"
                    icon="pi pi-times"
                    severity="danger"
                    @click="() => {searchText = undefined}"
                    v-tooltip="'Clear Search'"
                />
            </InputGroup>
            <div
                style="
                    display: flex;
                    flex-direction: column;
                    padding-top: 0.25rem;
                    padding-bottom: 0.25rem;
                    gap: 0.5rem;
                    width: 100%;
            ">
                <a :href="`/integrations?selected=new${sessionIdParam}`">
                    <Button
                        style="height: 32px"
                        icon="pi pi-plus"
                        label="Add New Integration"
                    />
                </a>
            </div>
            <div
                style="
                    display: flex;
                    flex-direction: column;
                    padding-top: 0.25rem;
                    padding-bottom: 0.25rem;
                    gap: 0.5rem;
                    width: 100%;
            ">
                <div>
                    <i>{{ integrations.length }} integrations available:</i>
                </div>
            </div>
        </div>
        <div class="integration-list">
            <div
                class="integration-card"
                v-for="(integration, index) in renderedIntegrations"
                :key="integration?.name"
                @mouseleave="hoveredIntegration = undefined"
                @mouseenter="hoveredIntegration = index"
            >
                <Card
                    :pt = "{
                        root: {
                            style:
                                'transition: background-color 150ms linear;' +
                                (hoveredIntegration === index
                                    ? 'background-color: var(--surface-100); cursor: pointer;'
                                    : '')
                        }
                    }"
                    @click="expandedIntegration = (expandedIntegration === index) ? undefined : index; "
                >
                    <template #title>
                        <div class="integration-card-title">
                            <span class="integration-card-title-text">
                                {{ integration?.name }}
                            </span>

                            <span v-if="expandedIntegration === index">
                                <a
                                    :href="`/integrations?selected=${integration?.slug}${sessionIdParam}`"
                                    v-tooltip="'Edit Integration'"
                                >
                                    <Button
                                        style="
                                            width: fit-content;
                                            height: 32px;
                                            margin-right: 0.5rem;
                                        "
                                        icon="pi pi-pencil"
                                        label="Edit"
                                    />
                                </a>
                            </span>
                        </div>
                    </template>
                    <template #content v-if="expandedIntegration === index">
                        <div
                            class="integration-main-content"
                            style="overflow: hidden;"
                            v-html="integration?.description ?? ''"
                        >
                        </div>
                    </template>
                </Card>
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from "vue";
import Button from "primevue/button";
import InputGroup from "primevue/inputgroup";
import InputGroupAddon from "primevue/inputgroupaddon";
import InputText from "primevue/inputtext";
import Card from "primevue/card";
import { marked } from "marked";

const searchText = ref(undefined);
const props = defineProps(["integrations"])

const urlParams = new URLSearchParams(window.location.search);
const sessionIdParam = urlParams.has("session") ? `&session=${urlParams.get("session")}` : "";

const sortedIntegrations = computed(() =>
    props?.integrations?.toSorted((a, b) => a?.name.localeCompare(b?.name)))

const filteredSortedIntegrations = computed(() => sortedIntegrations?.value?.filter(
    integration =>
        (searchText?.value === undefined)
        || integration?.name?.toLowerCase()?.includes(searchText?.value?.toLowerCase())
))

const renderedIntegrations = computed(() =>
    filteredSortedIntegrations?.value?.map(integration =>
        ({...integration, description: marked.parse(integration?.description ?? "")})
))

const expandedIntegration = ref<number|undefined>(undefined);
const hoveredIntegration = ref<number|undefined>(undefined);

const showTableOfContents = ref(false);

watch(searchText, () => {
    // if one result, fully show it
    if (filteredSortedIntegrations?.value?.length === 1) {
        expandedIntegration.value = 0;
        return;
    }
    expandedIntegration.value = undefined
})

</script>

<style lang="scss">
.integrations-panel {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    padding-left: 0.25rem;
    padding-right: 0.25rem;
    gap: 0.5rem;
    div.p-card .p-card-content {
        padding: 0;
    }
    div.p-card .p-card-title {
        margin-bottom: 0;
    }
    div.p-card-body {
        padding: 0.75rem 0.75rem;
    }
}

.integration-header {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.integration-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    overflow: auto;
    padding: 0.2rem;
}

.integration-card-title {
    display: flex;
    flex-direction: row;
    .integration-show-more {
        aspect-ratio: 1/1;
    }
    .integration-card-title-text {
        flex: 1 1;
        font-size: 1rem;
        font-weight: 500;
        margin: auto;
    }
}

.clickable-table-of-contents {
    &:hover, *:hover { cursor: pointer; color: var(--p-surface-h) }
    &:active, *:active { cursor: pointer; color: var(--p-surface-i) }
    * { margin-right: 0.2rem; }
}

// for inner h1 being larger than header; rescale to make sensible whitespace
.integration-main-content {
    margin-top: 0.5rem;
    h1 { font-size: 1.25rem; margin-bottom: 1rem;   }
    h2 { font-size: 1.2rem;  margin-bottom: 0.8rem; }
    h3 { font-size: 1.15rem; margin-bottom: 0.8rem; }
    h4 { font-size: 1.1rem;  margin-bottom: 0.8rem; }
    h5 { font-size: 1.05rem; margin-bottom: 0.8rem; }
    h6 { font-size: 1.0rem;  margin-bottom: 0.8rem; }
    p, ul, li { margin-bottom: 0.8rem; margin-top: 0rem; }
    h1, h2, h3, h4, h5, h6 {
        margin-top: 0.25rem;
    }
    > *:nth-child(1) {
        margin-top: 0rem;
    }

}
</style>
