<template>
    <div class="llm-query-cell">
        <div class="query-row">
            <div class="query">
                <div v-if="editing" style="display: flex">
                    <!-- TODO move ctrl/shift event stop on keyboard controller -->
                    <ContainedTextArea
                        style="max-width: 50%; margin-right: 0.75rem; flex: 1;"
                        @keydown.ctrl.enter.stop
                        @keydown.shift.enter.stop
                        v-model="editingContents"
                    />
                    <div class="edit-actions">
                        <Button outlined severity="success" label="Save" size="small" @click="saveEdit"/>
                        <Button outlined class="cancel-button" @click="cancelEdit" label="Cancel" size="small" />
                    </div>
                </div>
                <div v-else>
                    <div class="llm-prompt-container">
                        <p class="llm-prompt-text">{{ cell.source }}</p>
                        <p v-if="savedEdit" style="font-weight: 100;">(edited)</p>
                    </div>
                </div>
            </div>
            <div class="actions">
                <Button
                    text
                    size="small"
                    icon="pi pi-pencil"
                    severity="info"
                    @click="startEdit"
                />
                <Button
                    v-if="cell.status === 'busy'"
                    style="pointer-events: none;"
                    text
                    size="small"
                    severity="info"
                    icon="pi pi-spin pi-spinner"
                />
                <Button
                    v-else
                    style="pointer-events: none;"
                    text
                    size="small"
                    severity="success"
                    icon="pi pi-check-circle"
                />
            </div>
        </div>
        <div class="event-container" v-if="taggedCellEvents.length > 0">
            <div class="query-events-header">
                <span class="query-events-header-text">Agent Output</span>
            </div>
            <div class="events">
                <BeakerLLMQueryEvent
                    v-for="[eventIndex, event] of taggedCellEvents.entries()" 
                    :key="eventIndex"
                    :event="event"
                    :index="index"
                />
            </div>
        </div>
        <div
            class="input-request"
             v-focustrap
             v-if="cell.status === 'awaiting_input'"
         >
            <ContainedTextArea
                style="margin-right: 0.75rem; flex: 1;"
                autoFocus
                placeholder="Enter your response here"
                v-model="response"
                @keydown.ctrl.enter.stop
                @keydown.shift.enter.stop
                @submit="respond"
            />
            &nbsp;
            <Button
                outlined
                severity="success"
                size="small"
                label="reply"
                @click="respond"
            />
        </div>
    </div>

</template>

<script setup lang="ts">
import { defineProps, defineExpose, ref, shallowRef, inject, computed } from "vue";
import Button from "primevue/button";
import ContainedTextArea from './ContainedTextArea.vue';
import { BeakerBaseCell, BeakerSession } from 'beaker-kernel';
import BeakerLLMQueryEvent from "./BeakerLLMQueryEvent.vue";
import { BeakerQueryEvent } from "beaker-kernel/dist/notebook";

const props = defineProps([
    'index',
    'cell',
]);

const cell = shallowRef(props.cell);
const editing = ref(false);
const editingContents = ref("");
const savedEdit = ref("");
const response = ref("");
const session: BeakerSession = inject("session");

const taggedCellEvents = computed(() => {
    let index = 0;
    let events: BeakerQueryEvent[] = [...props.cell.events];
    for (const queryEvent of events) {
        if (queryEvent.type == "code_cell") {
            queryEvent.content.metadata.subindex = index;
            index += 1;
        }
    }
    return events;
});

function cancelEdit() {
    editing.value = false;
    editingContents.value = savedEdit.value || cell.value.source;
}

async function startEdit() {
    if (editing.value === true) {
        return;
    } // else [is]editing.value is false
    editing.value = true;
    editingContents.value = savedEdit.value || cell.value.source;

}

function saveEdit() {
    editing.value = false;
    savedEdit.value = editingContents.value;
    cell.value.source = editingContents.value;
}

const respond = () => {
    if (!response.value.trim()) {
        return; // Do nothing unless the reply has contents
    }
    props.cell.respond(response.value, session);
    response.value = "";
};

function execute() {
    const future = props.cell.execute(session);
}

defineExpose({execute});

</script>


<style lang="scss">
.llm-query-cell {
    padding: 0rem 0.35rem 1rem 1.2rem;
}

.query-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.events {
    padding: 0.25rem 0;
    display: flex;
    flex-direction: column;
}

.query {
    flex: 1;
    margin-bottom: 0.25rem;
}

.thought {
    color: var(--blue-500);
}

.response {
    margin-top: 0.75em;
    white-space: pre-line;
}

.input-request {
    padding: 0.5rem 0;
    display: flex;
    align-items: flex-start;
    width: 90%;
}

.actions {
    display: flex;
    .p-button-icon {
        font-weight: bold;
        font-size: 1rem;
    }
}

.edit-actions {
    display: flex;
    align-items: flex-start;
    .p-button {
        margin-right: 0.5rem;
    }
}

.cancel-button {
    border-color: var(--surface-100);
    color: var(--primary-text-color);
}


.llm-prompt-container {
    display: flex;
    flex-direction: column;
}

.llm-prompt-header {

}

.llm-prompt-text {
    margin-top: 0;
    margin-bottom: 0;
}

.event-container {
    margin-top: 1.25rem;
    padding: 0rem;
    border-radius: 6px;
    background-color: var(--surface-c);
}

.query-events-header {
    background-color: var(--surface-b);
    border-radius: 6px 6px 0 0;
}

.query-events-header {
    font-weight: 600;
}

</style>
