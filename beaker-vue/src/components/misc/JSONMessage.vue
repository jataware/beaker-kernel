<template>
  <div class="log-message">
    <Panel
        class="log-message-panel"
        v-if="logEntry?.body"
    >
        <template #header>
            <div class="log-message-header-container">
                <div class="log-message-title">
                    <div v-if=logEntry?.body?.parent_header?.msg_type >
                        <span style="font-weight: 500; text-wrap: nowrap;">
                            {{logEntry?.body?.parent_header?.msg_type}} >
                        </span>
                    </div>
                    <span style="font-weight: 500">
                        {{logEntry?.body?.header?.msg_type}}
                    </span>
                    <span>({{logEntry.type}})</span>
                </div>
                <span class="log-message-date">
                    {{ logEntry?.timestamp.split('T')[1].slice(0, -1) }}
                </span>
            </div>
        </template>

        <DataTable
            showGridlines
            stripedRows
            class="log-info-datatable"
            :value="Object.entries(logEntry?.body?.content).map(([key, value]) => ({key, value}))"
            v-if="logEntry?.body?.content && Object.keys(logEntry?.body?.content).length > 0"
        >
            <Column field="key"></Column>
            <Column field="value"></Column>
        </DataTable>
        <p v-else style="
            font-style: italic;
            color:var(--surface-400);
            margin-bottom: 0.5rem;
            margin-top: 0rem;
        ">
            (Empty body.)
        </p>

        <div
            class="log-dropdown log-dropdown-details"
            :onclick="() => {showDetails = !showDetails}"
        >
            <span class="pi" :class="{
                'pi-angle-right': !showDetails,
                'pi-angle-down': showDetails
            }"/>
            <span class="log-dropdown-label">
                {{showDetails ? 'Hide' : 'Show'}} Additional Details
            </span>
        </div>

        <div v-if="showDetails" class="log-dropdown-additional-details">
            <div
                class="log-dropdown log-dropdown-header"
                :onclick="() => {showHeader = !showHeader}"
            >
                <span class="pi" :class="{
                    'pi-angle-right': !showHeader,
                    'pi-angle-down': showHeader
                }"/>
                <span class="log-dropdown-label">
                    {{showHeader ? 'Hide' : 'Show'}} Header
                </span>
            </div>
            <div v-if="showHeader" class="log-dropdown-body">
                <DataTable
                    showGridlines
                    stripedRows
                    class="log-info-datatable"
                    :value="Object.entries(logEntry?.body?.header).map(([key, value]) => ({key, value}))"
                >
                    <Column field="key"></Column>
                    <Column field="value"></Column>
                </DataTable>
            </div>

            <div
                class="log-dropdown log-dropdown-parent-header"
                :onclick="() => {showParentHeader = !showParentHeader}"
            >
                <span class="pi" :class="{
                    'pi-angle-right': !showParentHeader,
                    'pi-angle-down': showParentHeader
                }"/>
                <span class="log-dropdown-label">
                    {{showParentHeader ? 'Hide' : 'Show'}} Parent Header
                </span>
            </div>
            <div v-if="showParentHeader" class="log-dropdown-body">
                <DataTable
                    showGridlines
                    stripedRows
                    class="log-info-datatable"
                    :value="Object.entries(logEntry?.body?.parent_header).map(([key, value]) => ({key, value}))"
                >
                    <Column field="key"></Column>
                    <Column field="value"></Column>
                </DataTable>
            </div>

            <div
                class="log-dropdown log-dropdown-raw"
                :onclick="() => {showRaw = !showRaw}"
            >
                <span class="pi" :class="{
                    'pi-angle-right': !showRaw,
                    'pi-angle-down': showRaw
                }"/>
                <span class="log-dropdown-label">
                    {{showRaw ? 'Hide' : 'Show'}} Raw Message (JSON)
                </span>
            </div>
            <div v-if="showRaw" class="log-dropdown-body">
                <vue-json-pretty
                    :data="logEntry.body"
                    :deep="2"
                    showLength
                    showIcon
                    :showDoubleQuotes="isQuotes"
                    :showLineNumber="linenum"
                />
            </div>
        </div>

        <div class="log-message-details">
            <span style="
                font-style: italic;
                color: var(--surface-400);
                font-size: 0.85rem;"
            >
                {{ logEntry?.body?.header?.msg_id }}
            </span>
        </div>
    </Panel>
  </div>
</template>
<script lang="ts" setup>

import { ref, computed } from "vue";
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';
import Panel from 'primevue/panel';
import DataTable from "primevue/datatable";
import Column from "primevue/column";

const props = defineProps([
    "logEntry",
    "options"
])

const isQuotes = computed(() => {
  return props.options?.value?.includes('quotes');
});

const linenum = computed(() => {
  return props.options?.value?.includes('linenum');
})

const showDetails = ref(false);

const showRaw = ref(false);
const showHeader = ref(false);
const showParentHeader = ref(false);

</script>

<style lang="scss">

.log-message-details-date {
    display: flex;
    flex-direction: row;
    gap: 0.5rem;
}

.log-message-panel {
    margin-top: 0.5rem;
    // margin-bottom: 0;
    position: relative;
    white-space: pre-wrap;

    .p-panel-header {
        background: var(--surface-b);
        padding: 0.5rem 1rem;
    }
    .p-panel-content {
        padding: 0.5rem 0.75rem;
    }
}

.log-message-header-container {
    width: 100%;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
}

.log-message-title {
    display: flex;
    flex-direction: row;
    gap: 0.2rem;
    flex: 0 1 auto;
    min-width: 0;
    flex-wrap: wrap;
}

.log-message-date {
    color: var(--grey-300);
    flex: 0 0 auto;
}

.log-dropdown {
    font-size: 0.9rem;
    display: flex;
    flex-direction: row;
    justify-content: flex-start;
    gap: 0.2rem;

    span.pi {
        font-size: 0.85rem;
    }
    * {
        margin: auto 0.2rem auto 0;
    }
    &:hover {
        cursor: pointer;
        .log-dropdown-label {
            text-decoration: underline;
        }
    }
}

.log-dropdown-additional-details {
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
}

.log-info-datatable {
    font-size: 0.85rem;
    margin-bottom: 0.5rem;
    thead.p-datatable-thead {
        display: none;
    }
    tbody tr td {
        padding: 0.2rem;
        font-family: monospace;
    }
    tbody tr:nth-child(1) td {
        border-top: 1px solid var(--surface-d);
    }
}

.log-dropdown-body {
    margin-top: 0.5rem;
}
</style>
