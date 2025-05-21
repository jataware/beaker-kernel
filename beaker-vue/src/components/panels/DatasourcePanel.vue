<template>
    <div class="datasources-panel">
        <div class="datasource-header">
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
                    <i>{{ datasources.length }} integrations available:</i>
                </div>
            </div>
        </div>
        <div class="datasource-list">
            <div
                class="datasource-card"
                v-for="(datasource, index) in renderedDatasources"
                :key="datasource?.name"
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
                        <div class="datasource-card-title">
                            <span class="datasource-card-title-text">
                                {{ datasource?.name }}
                            </span>

                            <span v-if="expandedIntegration === index">
                                <a
                                    :href="`/integrations?selected=${datasource?.slug}${sessionIdParam}`"
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
                            class="datasource-main-content"
                            style="overflow: hidden;"
                            v-html="datasource?.description ?? ''"
                        >
                        </div>
                    </template>
                </Card>
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, defineProps, computed, watch } from "vue";
import Button from "primevue/button";
import InputGroup from "primevue/inputgroup";
import InputGroupAddon from "primevue/inputgroupaddon";
import InputText from "primevue/inputtext";
import Card from "primevue/card";
import { marked } from "marked";

const searchText = ref(undefined);
const props = defineProps(["datasources"])

const urlParams = new URLSearchParams(window.location.search);
const sessionIdParam = urlParams.has("session") ? `&session=${urlParams.get("session")}` : "";

const sortedDatasources = computed(() =>
    props?.datasources?.toSorted((a, b) => a?.name.localeCompare(b?.name)))

const filteredSortedDatasources = computed(() => sortedDatasources?.value?.filter(
    datasource =>
        (searchText?.value === undefined)
        || datasource?.name?.toLowerCase()?.includes(searchText?.value?.toLowerCase())
))

const renderedDatasources = computed(() =>
    filteredSortedDatasources?.value?.map(datasource =>
        ({...datasource, description: marked.parse(datasource?.description ?? "")})
))

const expandedIntegration = ref<number|undefined>(undefined);
const hoveredIntegration = ref<number|undefined>(undefined);

const showTableOfContents = ref(false);

watch(searchText, () => {
    // if one result, fully show it
    if (filteredSortedDatasources?.value?.length === 1) {
        expandedIntegration.value = 0;
        return;
    }
    expandedIntegration.value = undefined
})

</script>

<style lang="scss">
.datasources-panel {
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

.datasource-header {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.datasource-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    overflow: auto;
    padding: 0.2rem;
}

.datasource-card-title {
    display: flex;
    flex-direction: row;
    .datasource-show-more {
        aspect-ratio: 1/1;
    }
    .datasource-card-title-text {
        flex: 1 1;
        font-size: 1rem;
        font-weight: 500;
        margin: auto;
    }
}

.clickable-table-of-contents {
    &:hover, *:hover { cursor: pointer; color: var(--surface-600) }
    &:active, *:active { cursor: pointer; color: var(--surface-800) }
    * { margin-right: 0.2rem; }
}

// for inner h1 being larger than header; rescale to make sensible whitespace
.datasource-main-content {
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
