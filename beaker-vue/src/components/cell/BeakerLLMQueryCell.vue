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
                        <h2 class="llm-prompt-text">{{ cell.source }}</h2>
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
                <h3 class="query-steps">Agent Steps:</h3>
                <div class="query-horizontal-br" />
                <Accordion :multiple="true" :class="'query-accordion'" v-model:active-index="selectedEvents">
                    <AccordionTab 
                        v-for="[eventIndex, event] of taggedCellEvents.entries()" 
                        :key="eventIndex"
                        :pt="{
                            header: {
                                class: [`query-tab`, `query-tab-${event.type}`]
                            },
                            headerAction: {
                                class: [`query-tab-headeraction`, `query-tab-headeraction-${event.type}`]
                            },
                            content: {
                                class: [`query-tab-content-${event.type}`]
                            },
                            headerIcon: {
                                class: [`query-tab-icon-${event.type}`]
                            }
                        }"
                    >
                        <template #header>
                            <span class="flex align-items-center gap-2 w-full">
                                <span :class="eventIconMap[event.type]"/>
                                <span class="font-bold white-space-nowrap">{{ queryEventNameMap[event.type] }}</span>
                            </span>
                        </template>
                        <BeakerLLMQueryEvent
                            :key="eventIndex"
                            :event="event"
                            :parentQueryCell="cell"
                        />
                    </AccordionTab>
                </Accordion>
                <div class="query-answer" v-if="isLastEventTerminal()" >
                    <h3 class="query-steps">Agent Response:</h3>
                    <BeakerLLMQueryEvent 
                        v-if="isLastEventTerminal()" 
                        :event="cell?.events[cell?.events.length - 1]" 
                        :parent-query-cell="cell"
                    />
                </div>
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
import { defineProps, defineExpose, ref, shallowRef, inject, computed, nextTick, onBeforeMount, getCurrentInstance, onBeforeUnmount } from "vue";
import Button from "primevue/button";
import Accordion from "primevue/accordion";
import AccordionTab from "primevue/accordiontab";
import BeakerLLMQueryEvent from "./BeakerLLMQueryEvent.vue";
import { BeakerQueryEvent, BeakerQueryEventType } from "beaker-kernel/dist/notebook";
import ContainedTextArea from '@/components/misc/ContainedTextArea.vue';
import { BeakerSession } from 'beaker-kernel';
import { BeakerSessionComponentType } from "../session/BeakerSession.vue";

const props = defineProps([
    'index',
    'cell',
]);

const eventIconMap = {
    "code_cell": "pi pi-align-left",
    "thought": "pi pi-comment",
    "user_answer": "pi pi-reply",
    "user_question": "pi pi-question-circle"
}

const terminalEvents = [
    "error",
    "response"
]

const cell = shallowRef(props.cell);
const focused = ref(false);
const response = ref("");
const textarea = ref();
const session: BeakerSession = inject("session");
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
const instance = getCurrentInstance();

const taggedCellEvents = computed(() => {
    let index = 0;
    const events: BeakerQueryEvent[] = [...props.cell.events];
    for (const queryEvent of events) {
        if (queryEvent.type == "code_cell") {
            queryEvent.content.metadata.subindex = index;
            index += 1;
        }
    }
    return events.filter((e) => !terminalEvents.includes(e.type));
});

const isLastEventTerminal = () => {
    const events: BeakerQueryEvent[] = props.cell.events;
    return terminalEvents.includes(events[events.length - 1].type);
};

// behavior: temporarily show last event and all code cells, until terminal, in which case,
// only show code cells
const selectedEvents = computed(() => {
    if (taggedCellEvents.value.length == 0) {
        return [0];
    }
    const events: BeakerQueryEvent[] = [...props.cell.events];
    const codeCellIndices = events
        .map((e, index) => e.type === "code_cell" ? index : null)
        .filter(e => e);
    if (isLastEventTerminal()) {
        return codeCellIndices;
    }
    return [...codeCellIndices, taggedCellEvents.value.length - 1];
})

const queryEventNameMap: {[eventType in BeakerQueryEventType]: string} = {
    "thought": "Agent Thought",
    "response": "Agent Response",
    "code_cell": "Code",
    "user_answer": "Answer",
    "user_question": "Question",
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
            textarea.value.$el.focus();
        });
    }
}

function exit() {
    // TODO
}

function clear() {
    // TODO
}

defineExpose({
    execute, 
    enter, 
    exit, 
    clear
});

onBeforeMount(() => {
    beakerSession.cellRegistry[cell.value.id] = instance.vnode;
});

onBeforeUnmount(() => {
    delete beakerSession.cellRegistry[cell.value.id];
});

</script>

<script lang="ts">
import { BeakerQueryCell } from "beaker-kernel";
export default {
    modelClass: BeakerQueryCell
};
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
    //background-color: var(--surface-c);
}

h3.query-steps {
    margin-bottom: 0rem;
}

.llm-prompt-text {
    margin-top: 0;
    margin-bottom: 0;
    font-weight: 400;
}

.event-container {
    //margin-top: 1.25rem;
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

.query-steps {
    font-weight: 400;
}

div.query-tab a.p-accordion-header-link.p-accordion-header-action{
    padding-left: 0px;
    background: none;
    border: none;
    padding-top: 1rem;
    padding-bottom: 0;
}

div.query-tab-thought a.p-accordion-header-link.p-accordion-header-action,
div.query-tab-user_question a.p-accordion-header-link.p-accordion-header-action,
div.query-tab-user_answer a.p-accordion-header-link.p-accordion-header-action {
    background: none;
    border: none;
    font-size: 0.75rem;
    font-weight: 400;
}

div.p-accordion-content.query-tab-content-thought,
div.p-accordion-content.query-tab-content-user_question,
div.p-accordion-content.query-tab-content-user_answer {
    background: none;
    border: none;
    font-size: 0.9rem;
    padding-left: 2.5rem;
}

div.p-accordion-content.query-tab-content-code_cell {
    background: none;
    border: none;
    padding-left: 2.5rem;
}

div.code-cell.query-event-code-cell {
    padding-left: 0;
}

svg.query-tab-icon-thought,
svg.query-tab-icon-user_answer,
svg.query-tab-icon-user_question {
    width: 1rem;
    height: 0.7rem; 
}

a.query-tab-headeraction > span > span.pi {
    align-items: center;
    margin: auto; 
    padding-right: 0.25rem;
}

a.query-tab-headeraction > span > span.pi-align-left {
    font-size: 1.2rem;
    font-weight: 500;
    margin: auto;
    padding-right: 0.6rem;
}

.query-answer {
    background-color: var(--surface-c);
    padding-left: 1rem;
    padding-bottom: 1rem;
    border-radius: 12px;
    margin-top: 1rem;
}


</style>