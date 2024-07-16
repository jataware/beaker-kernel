<template>
    <div class="llm-query-cell">
        <div class="query-row">
            <div class="query">
                <div v-show="focused">
                    <ContainedTextArea
                        ref="textarea"
                        style="max-width: 50%; margin-right: 0.75rem; flex: 1;"
                        v-model="cell.source"
                    />
                </div>
                <div v-show="!focused">
                    <div class="llm-prompt-container">
                        <p class="llm-prompt-text">{{ cell.source }}</p>
                    </div>
                </div>
            </div>
            <div class="actions">
                <Button
                    v-if="cell.status === 'busy'"
                    style="pointer-events: none;"
                    text
                    size="small"
                    severity="info"
                    icon="pi pi-spin pi-spinner"
                />
            </div>
        </div>
        <div class="event-container" v-if="taggedCellEvents.length > 0">
            <div class="events">
                <Accordion :multiple="true" :class="'query-accordion'">
                    <AccordionTab 
                        v-for="[eventIndex, event] of taggedCellEvents.entries()" 
                        :header="queryEventNameMap[event.type]"
                        :key="eventIndex"
                        :class="'query-accordiontab'"
                    >
                        <BeakerLLMQueryEvent
                            :key="eventIndex"
                            :event="event"
                            :index="index"
                            :queryCell="cell"
                        />
                    </AccordionTab>
                </Accordion>
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
import { defineProps, defineExpose, ref, shallowRef, inject, computed, nextTick } from "vue";
import Button from "primevue/button";
import Accordion from "primevue/accordion";
import AccordionTab from "primevue/accordiontab";
import ContainedTextArea from './ContainedTextArea.vue';
import { BeakerBaseCell, BeakerSession } from 'beaker-kernel';
import BeakerLLMQueryEvent from "./BeakerLLMQueryEvent.vue";
import { BeakerQueryEvent, BeakerQueryEventType } from "beaker-kernel/dist/notebook";

const props = defineProps([
    'index',
    'cell',
]);

const cell = shallowRef(props.cell);
const focused = ref(false);
const response = ref("");
const textarea = ref();
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

const queryEventNameMap: {[eventType in BeakerQueryEventType]: string} = {
    "thought": "Agent Thought",
    "response": "Agent Response",
    "code_cell": "Code",
    "user_answer": "User Input",
    "user_question": "User Input",
    "error": "Error",
    "abort": "Abort"
}

const respond = () => {
    if (!response.value.trim()) {
        return; // Do nothing unless the reply has contents
    }
    props.cell.respond(response.value, session);
    response.value = "";
};

function execute() {
    focused.value = false;
    const future = props.cell.execute(session);
}

function enter() {
    if (!focused.value) {
        focused.value = true;
        nextTick(() => {
            console.log(textarea);
            textarea.value.$el.focus();
        });
    }
}

defineExpose({execute, enter});

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

.llm-prompt-text {
    margin-top: 0;
    margin-bottom: 0;
}

.event-container {
    margin-top: 1.25rem;
    padding: 0rem;
    border-radius: 6px;
    //background-color: var(--surface-c);
}

.query-events-header {
    background-color: var(--surface-b);
    border-radius: 6px 6px 0 0;
}

.query-events-header {
    font-weight: 600;
}

.query-accordion .p-accordion-content {
    padding-top: 0.25rem;
    padding-bottom: 0rem;
}

</style>
