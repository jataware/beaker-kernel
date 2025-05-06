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
                        outlined
                    >
                        Add New Integration
                    </Button>
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
                <div
                    class="clickable-table-of-contents"
                    @click="showTableOfContents = !showTableOfContents"
                >
                    <i
                        :class="`pi ${showTableOfContents ? 'pi-chevron-down' : 'pi-chevron-right'}`"
                        style="margin-right: 0.2rem;"
                    >
                    </i>
                    <i>{{ datasources.length }} integrations loaded:</i>
                    <span>{{ showTableOfContents ? 'Hide Names' : 'Show Names' }}</span>
                </div>
                <div
                    v-if="showTableOfContents"
                    style="
                        border-radius: var(--border-radius);
                        border: 1px solid var(--surface-200);
                        padding: 0.25rem;
                        width: 100%;
                        height: 12rem;
                        overflow-y: auto;
                    "
                >
                    <ul>
                        <li v-for="datasource in sortedDatasources" :key="datasource?.name">
                            {{ datasource?.name }}
                        </li>
                    </ul>
                </div>

            </div>
        </div>
        <div class="datasource-list">
            <div class="datasource-card" v-for="(datasource, index) in renderedDatasources" :key="datasource?.name">
                <Card>
                    <template #title>
                        <div class="datasource-card-title">
                            <span class="datasource-card-title-text">
                                {{ datasource?.name }}
                            </span>
                            <span>
                                <a
                                    :href="`/integrations?selected=${datasource?.slug}${sessionIdParam}`"
                                    v-tooltip="'Edit Integration'"
                                >
                                    <Button
                                        style="
                                            width: 32px;
                                            height: 32px;
                                            margin-right: 0.5rem;
                                        "
                                        outlined
                                        icon="pi pi-pencil"
                                    />
                                </a>
                                <Button
                                    style="
                                        width: 32px;
                                        height: 32px;
                                    "
                                    outlined
                                    :icon="`pi ${cardState[index] ? 'pi-chevron-down' : 'pi-chevron-right'}`"
                                    @click="cardState[index] = !cardState[index]"
                                    v-tooltip="cardState[index] ? 'Show Less' : 'Show More'"
                                />
                            </span>
                        </div>
                    </template>
                    <template #content>
                        <div
                            class="datasource-main-content"
                            :style="`
                                overflow: hidden;
                                ${cardState[index] ? '' : 'height: 6rem;'}
                            `"
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
import { ref, computed, watch } from "vue";
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

const cardState = ref<boolean[]>([]);

const showTableOfContents = ref(false);

watch(searchText, () => {
    // if one result, fully show it
    if (filteredSortedDatasources?.value?.length === 1) {
        cardState.value[0] = true;
        return;
    }
    // otherwise rehide everything
    for (let i = 0; i < cardState?.value?.length; ++i) {
        cardState.value[i] = false;
    }
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
        padding: 0.25rem 0;
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
    // top card box shadow
    padding-top: 0.2rem;
    padding-bottom: 0.2rem;
}

.datasource-card-title {
    display: flex;
    flex-direction: row;
    .datasource-show-more {
        aspect-ratio: 1/1;
    }
    .datasource-card-title-text {
        flex: 1 1;
        font-size: 1.3rem;
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
