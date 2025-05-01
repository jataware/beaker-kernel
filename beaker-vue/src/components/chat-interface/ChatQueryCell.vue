<template>
    <div class="llm-query-cell">
        <div
            class="query query-chat"
            @dblclick="promptDoubleClick"
        >
            <div class="llm-prompt-container llm-prompt-container-chat">
                <div v-show="isEditing" class="prompt-input-container">
                    <ContainedTextArea
                        ref="textarea"
                        class="prompt-input"
                        v-model="promptText"
                        :style="{minHeight: `${promptEditorMinHeight}px`}"
                    />
                    <div class="prompt-controls" style="">
                        <Button label="Submit" @click="execute"/>
                        <Button label="Cancel" @click="promptText = cell.source; isEditing = false"/>
                    </div>
                </div>
                <div
                    v-show="!isEditing"
                    class="llm-prompt-text llm-prompt-text-chat"
                    :data-cell-id="cell.id"
                >{{ cell.source }}</div>
            </div>
        </div>
        <div class="event-container"
            v-if="events.length > 0 || isLastEventTerminal() || showChatEventsEarly(cell)"
        >
            <div class="events">
                <div
                    class="expand-thoughts-button"
                    :class="{ 'expanded': session.notebook.selectedCell === cell }"
                    @click="expandThoughts"
                >
                    <div 
                        class="white-space-nowrap"
                        style="
                            display: flex; 
                            align-items: center;
                            font-weight: 400;
                            font-family: 'Courier New', Courier, monospace;
                            font-size: 0.8rem;
                            color: var(--text-color-secondary)
                        "
                    >
                        <i
                            class="pi pi-sparkles"
                            :class="{'animate-sparkles': queryStatus === QueryStatuses.Running}"
                            style="
                                color: var(--yellow-500);
                                font-size: 1.25rem;
                                margin-right: 0.6rem;
                            "
                        />
                        {{ lastEventThought }}
                    </div>
                    <Button 
                      :icon="session.notebook.selectedCell === cell ? 'pi pi-times' : 'pi pi-search'"
                      text 
                      rounded 
                      style="background-color: var(--surface-c); color: var(--text-color-secondary); width: 2rem; height: 2rem; padding: 0;"
                    />
                </div>
                <div v-for="[messageEvent, messageClass] of messageEvents" v-bind:key="messageEvent.id">
                    <div style="display: flex; flex-direction: column;">
                        <BeakerQueryCellEvent
                            :event="messageEvent"
                            :parent-query-cell="cell"
                            :class="messageClass"
                        />
                    </div>
                </div>
                <div 
                    class="query-answer-chat-override"
                    v-if="isLastEventTerminal()"
                >
                    <BeakerQueryCellEvent
                        :event="cell?.events[cell?.events.length - 1]"
                        :parent-query-cell="cell"
                    />
                </div>
            </div>
        </div>
        <div
            class="input-request-chat-override"
            v-focustrap
            v-if="cell.status === 'awaiting_input'"
         >
            <div
                class="input-request-wrapper input-request-wrapper-chat"
            >
                <InputGroup>
                    <InputGroupAddon>
                        <i class="pi pi-exclamation-triangle"></i>
                    </InputGroupAddon>
                    <InputText
                        placeholder="Reply to the agent"
                        @keydown.enter.exact.prevent="respond"
                        @keydown.escape.prevent.stop="($event.target as HTMLElement).blur()"
                        @keydown.ctrl.enter.stop
                        @keydown.shift.enter.stop
                        autoFocus
                        v-model="response"
                    />
                    <Button
                        icon="pi pi-send"
                        @click="respond"
                    />
                </InputGroup>
            </div>
        </div>
    </div>

</template>

<script setup lang="ts">
import { defineProps, defineExpose, ref, shallowRef, inject, computed, nextTick, onBeforeMount, getCurrentInstance, onBeforeUnmount, watch } from "vue";
import Button from "primevue/button";
import InputGroup from 'primevue/inputgroup';
import InputText from 'primevue/inputtext';
import InputGroupAddon from 'primevue/inputgroupaddon';
import { BeakerQueryEvent, type BeakerQueryEventType } from "beaker-kernel/src/notebook";
import { BeakerSession } from 'beaker-kernel/src';
import BeakerQueryCellEvent from "../cell/BeakerQueryCellEvent.vue";
import ContainedTextArea from '../misc/ContainedTextArea.vue';
import { BeakerSessionComponentType } from "../session/BeakerSession.vue";


const props = defineProps([
    'index',
    'cell',
]);

const terminalEvents = [
    "error",
    "response"
]

const enum QueryStatuses {
    NotExecuted,
    Running,
    Done,
}

const cell = shallowRef(props.cell);
const isEditing = ref<boolean>(cell.value.source === "");
const promptEditorMinHeight = ref<number>(100);
const promptText = ref<string>(cell.value.source);
const response = ref("");
const textarea = ref();
const hasExpandedThoughts = ref(false);
const session: BeakerSession = inject("session");
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");

const instance = getCurrentInstance();


const events = computed(() => {
    return [...props.cell.events];
})

const lastEventThought = computed(() => {
    const fallback = "Thinking";
    // initial state
    if (events.value.length < 1) {
        return fallback;
    }
    // grab the text from the last thought.
    const lastEvent = events.value[events.value.length - 1];
    if (lastEvent.type === 'thought') {
        return lastEvent.content.thought;
    }
    else {
        // walk backwards through events to determine the last thought
        let offset = 2;
        let eventCursor = events.value[events.value.length - offset];
        if (eventCursor === undefined) {
            return fallback;
        }
        while (eventCursor.type !== 'thought' && events.value.length >= offset) {
            offset += 1;
            eventCursor = events.value[events.value.length - offset];
        }
        if (eventCursor.type === 'thought') {
            if (eventCursor.content.thought === "Thinking..." && lastEvent.type === "response") {
                return "Done";
            }
            const endTags = {
                'user_question': "(awaiting user input)",
                'user_answer': "(answer received, thinking)",
                'code_cell': "(code is now running)",
            }
            if (endTags[lastEvent.type]) {
                return `${eventCursor.content.thought} ${endTags[lastEvent.type]}`;
            }
            else {
                return eventCursor.content.thought;
            }
        // no thought, end of stack
        } else {
            return fallback;
        }
    }
})

const expandThoughts = () => {
    if (session.notebook.selectedCell === cell.value) {
        session.notebook.selectedCell = undefined;
    } else {
        session.notebook.selectedCell = cell.value;
    }
};

const queryStatus = computed<QueryStatuses>(() => {
    const eventCount = events.value.length;
    if (props.cell.status === 'busy') {
        return QueryStatuses.Running;
    }
    if (eventCount === 0) {
        return QueryStatuses.NotExecuted;
    }
    else if (terminalEvents.includes(events.value[eventCount - 1].type)) {
        return QueryStatuses.Done;
    }
    else {
        return QueryStatuses.Running;
    }
})

watch(queryStatus, (newStatus, oldStatus) => {
     // Auto-expand thoughts the first time a cell transitions to Running
     if (newStatus === QueryStatuses.Running && oldStatus !== QueryStatuses.Running && !hasExpandedThoughts.value) {
        expandThoughts();
        hasExpandedThoughts.value = true;
     }
})


const messageEvents = computed(() => {
    return props.cell?.events?.filter(
        (event) => ["user_question", "user_answer"].includes(event.type)
    ).map(
        (event) => {
            var messageClass;
            if (event.type === "user_question") {
                messageClass = "query-answer-chat query-answer-chat-override";
            }
            else {
                messageClass = "llm-prompt-container llm-prompt-container-chat llm-prompt-text llm-prompt-text-chat";
            }
            return [event, messageClass];
        }
    );
})

const showChatEventsEarly = (cell) => cell.status === 'busy';

const isLastEventTerminal = () => {
    const events: BeakerQueryEvent[] = props.cell.events;
    if (events?.length > 0) {
        return terminalEvents.includes(events[events.length - 1].type);
    }
    return false;
};


// const queryEventNameMap: {[eventType in BeakerQueryEventType]: string} = {
//     "thought": "Thought",
//     "response": "Final Response",
//     "code_cell": "Code",
//     "user_answer": "Answer",
//     "user_question": "Question",
//     // "background_code": "Background Code",
//     "error": "Error",
//     "abort": "Abort"
// }

const promptDoubleClick = (event) => {
    if (!isEditing.value) {
        promptEditorMinHeight.value = (event.target as HTMLElement).clientHeight;
        isEditing.value = true;
    }
}

const respond = () => {
    if (!response.value.trim()) {
        return; // Do nothing unless the reply has contents
    }
    props.cell.respond(response.value, session);
    response.value = "";
};

function execute() {
    const config: any = instance?.root?.props?.config;
    const sendNotebookState = config ? config.extra?.send_notebook_state : undefined;
    cell.value.source = promptText.value;
    isEditing.value = false;
    nextTick(() => {
        const future = props.cell.execute(session, sendNotebookState);
        // Add reference to cell for downstream processing.
        future.registerMessageHook(
            (msg) => {
                msg.cell = cell.value;
            }
        )
    });
}

function enter(position?: "start" | "end" | number) {
    if (!isEditing.value) {
        isEditing.value = true;
    }
    if (position === "start") {
        position = 0;
    }
    else if (position === "end") {
        position = textarea.value?.$el?.value.length || -1;
    }
    nextTick(() => {
        textarea.value?.$el?.focus();
        textarea.value.$el.setSelectionRange(position, position);
    });
}

function exit() {
    if (promptText.value === cell.value.source) { // Query has not changed
        isEditing.value = false;
    }
    else {
        textarea.value?.$el?.blur();
    }
}

function clear() {
    cell.value.source = "";
    isEditing.value = true;
    promptEditorMinHeight.value = 100;
    promptText.value = "";
    response.value = "";
}

defineExpose({
    execute,
    enter,
    exit,
    clear,
    cell,
    editor: textarea,
});

onBeforeMount(() => {
    beakerSession.cellRegistry[cell.value.id] = instance.vnode;
});

onBeforeUnmount(() => {
    delete beakerSession.cellRegistry[cell.value.id];
});

</script>

<script lang="ts">
import { BeakerQueryCell } from "beaker-kernel/src";
export default {
    modelClass: BeakerQueryCell,
    icon: "pi pi-sparkles",
};
</script>


<style lang="scss">

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
    display: flex;
    justify-content: space-between;
    flex-direction: column;
    margin-bottom: 0.25rem;
}

.query-chat {
    align-items: flex-end;
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

.input-request-wrapper {
    display: flex;
    width: 100%;
}

.input-request-chat-override {
    align-items: flex-end;
    width: 100%;
    .input-request-wrapper-chat {
        align-items: flex-end;
        flex-direction: column;
        .p-inputgroup {
            width: 100%;
            border: 1px solid var(--yellow-500);
            box-shadow: 0 0 4px var(--yellow-700);
            transition: box-shadow linear 1s;
            border-radius: var(--border-radius);
            button {
                background-color: var(--surface-b);
                border-color: var(--surface-border);
                color: var(--text-color);
                border-left: 0px;
            }
            input {
                border-color: var(--yellow-500);
            }
        }
        margin-bottom: 0.5rem;
    }
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
    background-color: var(--surface-c);
    border-radius: var(--border-radius);
}

.llm-prompt-container-chat {
    width: fit-content;
    max-width: 80%;
    align-self: flex-end;
    background-color: var(--surface-d);
}

div.query-steps {
    margin-bottom: 1rem;
}

h3.query-steps {
    margin-bottom: 0rem;
}

.llm-prompt-text {
    margin-left: 1rem;
    padding: 0.5rem;
    white-space: pre-wrap;
    width: fit-content;
}

.llm-prompt-text-chat {
    margin-left: 0.5rem;
    margin-right: 0.5rem;
}

.event-container {
    padding: 0rem;
    border-radius: 6px;
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

.query-accordion-chat {
    margin-bottom: 0.5rem;
    width: 100%;
    > .p-accordion-tab {
        > * {
            max-width: 80%;
            width: 100%;
        }
        width: 100%;
        display: flex;
        align-items: center;
        flex-direction: column;
        > .p-toggleable-content > .p-accordion-content {
            border: 2px solid var(--surface-d);
            border-radius: var(--border-radius);
            padding: 0.25rem;
            padding-left: 1.5rem;
            margin: 1rem;
            margin-bottom: 0rem;
            > * {
                border-bottom: 2px solid var(--surface-d);
                margin-right: 1rem;
            }
            > *:last-child {
                border-bottom: none;
            }
        }
        .p-accordion-header {
            border-radius: var(--border-radius);
            margin: 1rem;
            margin-bottom: 0rem;
            transition: background-color 0.2s;

            &:hover {
                background-color: var(--surface-a);
            }
        }
    }

}

.query-tab-title-chat {
    font-weight: 400;
}

.query-tab-thought-chat {
    .p-accordion-header-link svg {
        flex-shrink: 0;
    }
}

.query-steps {
    font-size: large;
}

.query-tab-background_code {
    font-size: 6pt;
    color: #777;

    + a {
        margin: 0;
        padding: 0;
    }
}


div.query-tab a.p-accordion-header-link.p-accordion-header-action{
    padding: 0.5rem;
    background: none;
    border: none;
}

div.query-tab-thought a.p-accordion-header-link.p-accordion-header-action,
div.query-tab-user_question a.p-accordion-header-link.p-accordion-header-action,
div.query-tab-user_answer a.p-accordion-header-link.p-accordion-header-action {
    background: none;
    border: none;
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


a.query-tab-headeraction > span > span.pi {
    align-items: center;
    margin: auto;
    padding-right: 0.5rem;
}

.query-answer {
    background-color: var(--surface-c);
    padding-left: 1rem;
    padding-bottom: 1rem;
    border-radius: var(--border-radius);
    margin-top: 1rem;
}

.query-answer-chat-override {
    padding-left: 1rem;
    padding-right: 1rem;
    border-radius: var(--border-radius);
    margin-top: 0.5rem;
    max-width: 80%;
    width: fit-content;
    background-color: var(--surface-c);

    margin-bottom: 1rem;
}

.prompt-input-container {
    display: flex;
    flex-direction: row;
}

.prompt-input {
    flex: 1;
}

.prompt-controls {
    display: flex;
    align-self: end;
    flex-direction: column;
    gap: 0.5em;
    margin: 0.5em;
}

.thought-icon {
    display: inline-block;
    height: 1rem;
    margin: auto;
    margin-right: 0.5rem;
    svg {
        fill: currentColor;
        stroke: currentColor;
        width: 1rem;
        margin: 0;
    }
}

.thinking-indicator {
    opacity: 0.7;
    vertical-align: middle;
}

.thinking-animation {
    font-size: x-large;
    clip-path: view-box;
}

.thinking-animation:after {
    overflow: hidden;
    display: inline-block;
    vertical-align: bottom;
    position: relative;
    animation: thinking-ellipsis 2000ms steps(48, end) infinite;
    content: "\2026\2026\2026\2026"; /* ascii code for the ellipsis character */
    width: 4em;
}


@keyframes thinking-ellipsis {
  from {
    right: 4em;
  }
  to {
    right: -4em;
  }
}

.expand-thoughts-button {
    cursor: pointer;
    border-radius: var(--border-radius);
    margin: auto;
    display: block;
    padding: 0.75rem;

    max-width: 80%;
    width: 100%;

    &:hover {
        background-color: var(--surface-b);
    }

    [data-theme="dark"] &:hover {
        background-color: var(--surface-a);
    }

    &.expanded {
        background-color: var(--surface-b);
    }

    display: flex;
    justify-content: space-between;

    & > div {
        flex: 1;
    }

    &>button {
        align-self: center;
    }
}

@keyframes sparkle-spin-bounce {
  0% {
    transform: rotate(0deg);
  }
  50% {
    transform: rotate(360deg);
  }
  60% {
    transform: rotate(360deg) translateY(-5px);
  }
  70% {
    transform: rotate(360deg) translateY(0px);
  }
  80% {
    transform: rotate(360deg) translateY(-3px);
  }
  90% {
    transform: rotate(360deg) translateY(0px);
  }
  100% {
    transform: rotate(360deg);
  }
}

.animate-sparkles {
  display: inline-block;
  animation: sparkle-spin-bounce 2s ease-in-out infinite;
  transform-origin: center;
}

</style>