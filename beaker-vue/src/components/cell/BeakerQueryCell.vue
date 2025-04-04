<template>
    <div class="llm-query-cell">
        <div
            class="query"
            :class="{
                'query-chat': isChat
            }"
            @dblclick="promptDoubleClick"
        >
            <div v-if="!isChat" class="query-steps">User Query:</div>
            <div
                class="llm-prompt-container"
                :class="{
                            'llm-prompt-container-chat': isChat
                        }"
            >
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
                    class="llm-prompt-text"
                    :class="{
                        'llm-prompt-text-chat': isChat
                    }"
                >{{ cell.source }}</div>
            </div>
        </div>
        <div class="event-container"
            v-if="events.length > 0 || isLastEventTerminal() || showChatEventsEarly(cell)"
        >
            <div class="events">
                <div
                    class="query-steps agent-actions-header"
                    v-if="events.length > 0 && !isChat"
                    @click="toggleThoughtsVisibility"
                >
                    <div class="agent-actions-toggle">
                        <i class="pi" :class="showThoughts ? 'pi-chevron-down' : 'pi-chevron-right'"></i>
                        <span class="agent-actions-toggle-text">Agent Actions</span>
                    </div>
                </div>
                <Accordion
                    v-if="events.length > 0 && !isChat && false"
                    :multiple="true"
                    :class="'query-accordion'"
                    v-model:active-index="selectedEvents"
                >
                    <AccordionTab
                        v-for="(event, eventIndex) in events"
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
                                <span :class="eventIconMap[event.type]">
                                    <ThinkingIcon v-if="event.type === 'thought'" class="thought-icon"/>
                                </span>
                                <span class="font-bold white-space-nowrap">{{ queryEventNameMap[event.type] }}</span>
                            </span>
                        </template>
                        <div style="border: 0px solid transparent;"> <!-- red -->
                            <BeakerQueryCellEvent
                                :key="eventIndex"
                                :event="event"
                                :parentQueryCell="cell"
                            />
                        </div>
                    </AccordionTab>
                </Accordion> 
                <div
                    v-if="thoughts.length > 0 && !isChat && showThoughts" 
                    class="thoughts-list"
                >
                    <div 
                        v-for="(thought, thoughtIndex) in thoughts" 
                        :key="thoughtIndex"
                        class="thought-item"
                        :class="{
                            'thought-item-alt': thoughtIndex % 2 === 1,
                            'thought-item-selected': expandedThoughts.has(thoughtIndex)
                        }"
                        @click="toggleCodeCellForThought(thoughtIndex)"
                    >
                        <div class="thought-content">
                            <span class="thought-icon"><ThinkingIcon/></span>
                            {{ thought.content.thought }}
                        </div>
                        <div v-if="expandedThoughts.has(thoughtIndex) && relatedCodeCells.get(thoughtIndex)" class="related-code-cell">
                            <div class="code-cell-controls">
                              <!-- <Button
                                size="small"
                                text
                                label="Move Out"
                                icon="pi pi-file-export"
                                @click.stop="addCodeCellToNotebook(relatedCodeCells.get(thoughtIndex))"
                              ></Button> -->
                                <Button 
                                    :icon="expandedCodeCells.get(thoughtIndex) ? 'pi pi-sort-up' : 'pi pi-expand'" 
                                    size="small"
                                    text
                                    class="code-cell-toggle-button" 
                                    @click.stop="toggleCodeCellExpansion($event, thoughtIndex)"
                                    :title="expandedCodeCells.get(thoughtIndex) ? 'Shrink code cell' : 'Expand code cell'"
                                />
                            </div>
                            <div :class="{'code-cell-collapsed': !expandedCodeCells.get(thoughtIndex)}">
                                <BeakerQueryCellEvent
                                    :event="relatedCodeCells.get(thoughtIndex)"
                                    :parent-query-cell="cell"
                                />
                            </div>
                        </div>
                    </div>
                </div>
                <div>
                <!-- <Button
                    size="small"
                    text
                    label="Move Out"
                    icon="pi pi-file-export"
                    @click.stop=""
                  ></Button> -->
                </div>
                <div
                    v-if="isChat"
                    class="expand-thoughts-button"
                    :class="{ 'expanded': session.notebook.selectedCell === cell }"
                    @click="expandThoughts"
                >
                    <div style="display: flex; align-items: center;">
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
                    <Button>{{ session.notebook.selectedCell === cell ? 'Close' : 'Details' }}</Button>
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
                <div :class="{
                        'query-answer': !isChat,
                        'query-answer-chat-override': isChat
                    }"
                    v-if="isLastEventTerminal()"
                >
                    <h3 v-show="!isChat" class="query-steps">Result</h3>
                    <BeakerQueryCellEvent
                        :event="cell?.events[cell?.events.length - 1]"
                        :parent-query-cell="cell"
                    />
                </div>
            </div>
        </div>
        <div class="thinking-indicator" v-if="cell.status === 'busy' && !isChat">
            <span class="thought-icon"><ThinkingIcon/></span> Thinking <span class="thinking-animation"></span>
        </div>
        <div
            :class="{
                'input-request': !isChat,
                'input-request-chat-override': isChat
            }"
            v-focustrap
            v-if="cell.status === 'awaiting_input'"
         >
            <div
                class="input-request-wrapper"
                :class="{
                    'input-request-wrapper-chat': isChat
                }"
            >
                <InputGroup>
                    <InputGroupAddon v-show="isChat">
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
import { IBeakerCell, BeakerSession } from 'beaker-kernel/src';
import { defineProps, defineExpose, ref, shallowRef, inject, computed, nextTick, onBeforeMount, getCurrentInstance, onBeforeUnmount, toRaw, watch, defineEmits, onMounted } from "vue";
import Button from "primevue/button";
import Accordion from "primevue/accordion";
import AccordionTab from "primevue/accordiontab";
import BeakerQueryCellEvent from "./BeakerQueryCellEvent.vue";
import { BeakerQueryEvent, type BeakerQueryEventType } from "beaker-kernel/src/notebook";
import ContainedTextArea from '../misc/ContainedTextArea.vue';
import { BeakerSessionComponentType } from "../session/BeakerSession.vue";
import { BeakerNotebookComponentType } from "../notebook/BeakerNotebook.vue";
import ThinkingIcon from "../../assets/icon-components/BrainIcon.vue";
import { StyleOverride } from "../../pages/BaseInterface.vue"

import InputGroup from 'primevue/inputgroup';
import InputText from 'primevue/inputtext';
import InputGroupAddon from 'primevue/inputgroupaddon';


const props = defineProps([
    'index',
    'cell',
]);

const eventIconMap = {
    "code_cell": "pi pi-code",
    "thought": "thought-icon",
    "user_answer": "pi pi-reply",
    "user_question": "pi pi-question-circle"
}

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
const session: BeakerSession = inject("session");
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
// const notebook = inject<BeakerNotebookComponentType>("notebook");
const showThoughts = ref(true);
// const selectedThoughtIndex = ref<number | null>(null);
const relatedCodeCell = ref<BeakerQueryEvent | null>(null);
// const codeCellExpanded = ref(true);

// Add flag to track if we've expanded thoughts already
const hasExpandedThoughts = ref(false);

// Add this new state to track multiple expanded thoughts
const expandedThoughts = ref<Set<number>>(new Set());
const expandedCodeCells = ref<Map<number, boolean>>(new Map());

const styleOverrides = inject<StyleOverride[]>("styleOverrides")
const isChat = ref(styleOverrides.includes('chat'))

const instance = getCurrentInstance();

const emit = defineEmits(['updateTitle']);

// can filter event types here, depending on what's selected
const events = computed(() => {
    return [...props.cell.events];
    // return [...props.cell.events].filter((event) => {
    //     if (event.type === 'code_cell') {
    //         return false;
    //     }
    //     return true;
    // });
});

const thoughts = computed(() => {
    return events.value.filter((event) => {
        if (event.type === 'thought') {
            return event;
        }
    });
});

const codeCells = computed(() => {
    return events.value.filter((event) => {
        if (event.type === 'code_cell') {
            return event;
        }
    });
});


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
            if (endTags[lastEvent.type]) { // There may be some missing types (eg error?)
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

// const addCodeCellToNotebook = (codeCell: BeakerQueryEvent) => {
//     console.log("addCodeCellToNotebook; raw cell:", toRaw(codeCell));
    
//     // Log methods and properties of the session object
//     console.log("Session methods:", Object.getOwnPropertyNames(Object.getPrototypeOf(session)));
//     console.log("Session properties:", Object.keys(session));
    
//     // For notebook object too
//     console.log("Notebook methods:", Object.getOwnPropertyNames(Object.getPrototypeOf(notebook)));
//     console.log("Notebook properties:", Object.keys(notebook));

//     // session.addCodeCell();

//     let copiedCellValue = toRaw(codeCell);

//     console.log("copiedCellValue", copiedCellValue);

//     if (copiedCellValue !== null) {
//         var newCell: IBeakerCell;

//         // If a cell with the to-be-pasted cell's id already exists in the notebook, set the copied cell's id to
//         // undefined so that it is regenerated when added.
//         const notebookIds = session.notebook.cells.map((cell) => cell.id);
//         console.log("notebookIds", notebookIds);

//         if (notebookIds.includes(copiedCellValue.id)) {

//             const cls = copiedCellValue.constructor as (data: IBeakerCell) => void;
//             const data = {
//                 ...copiedCellValue,
//                 // Set non-transferable attributes to undefined.
//                 id: undefined,
//                 executionCount: undefined,
//                 busy: undefined,
//                 last_execution: undefined,
//             } as IBeakerCell;
//             copiedCellValue = new cls(data);
//         }
//         // TODO doesnt work- check diff between all session/notebook types
//         // newCell = notebook.insertCellAfter(notebook.selectedCell(), copiedCellValue);
//         // console.log("session keys", Object.keys(session));

//         // notebook.insertCodeCell(copiedCellValue);
//         // notebook.insertCell(copiedCellValue);
//         notebook.insertCellAfter(notebook.selectedCell(), copiedCellValue);
//         // session.addCodeCell(copiedCellValue);
//     }

//     // notebook.insertCellAfter(codeCell.content.code);
//     // session.
//     // const codeCellEvent = codeCell as BeakerQueryEvent;
//     // console.log("codeCellEvent", codeCellEvent);
//     // const codeCellIndex = codeCellEvent.content.metadata.subindex;
//     // const codeCell = notebook.getCell(codeCellIndex);
//     // console.log("codeCell", codeCell);
// }

/* TODO What is a tagged cell event? */
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

const queryStatus = computed<QueryStatuses>(() => {
    // console.log("queryStatus computed; cell status:", props.cell.status);
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

function generateTitle(title: string) {
    // Don't mutate props directly
    // props.cell.valuesummaryTitle = title;
    console.log("emitting title:", title);
    console.log("cell id:", props.cell.id);
    emit('updateTitle', { cellId: props.cell.id, title });
    // console.log("generated title:", title);
}

watch(queryStatus, (newStatus, oldStatus) => {
    // console.log("queryStatus changed; new status:", newStatus, "prev status:", oldStatus);
     if (newStatus === QueryStatuses.Done && !props.cell.summaryTitle) {
        generateTitle(lastEventThought.value);
     }
     
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

const showChatEventsEarly = (cell) => isChat.value ? (cell.status === 'busy') : false;

const isLastEventTerminal = () => {
    const events: BeakerQueryEvent[] = props.cell.events;
    if (events?.length > 0) {
        return terminalEvents.includes(events[events.length - 1].type);
    }
    return false;
};

// behavior: temporarily show last event and all code cells, until terminal, in which case,
// only show code cells
const selectedEvents = computed({
    get() {
        const eventCount = events.value.length;
        if (eventCount === 0) {
            return [];
        }
        else if (eventCount === 1) {
            return [0];
        }
        else {
            return [eventCount-2, eventCount-1];
        }
    },
    set(newValue) {
        // no operation,
    },

})

const queryEventNameMap: {[eventType in BeakerQueryEventType]: string} = {
    "thought": "Thought",
    "response": "Final Response",
    "code_cell": "Code",
    "user_answer": "Answer",
    "user_question": "Question",
    // "background_code": "Background Code",
    "error": "Error",
    "abort": "Abort"
}

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

const expandThoughts = () => {
    // session is already injected...
    // const sessionId = session.sessionId;
    // console.log("sessionID", sessionId);

    // console.log("session.notebook.selectedCell", session.notebook.selectedCell);
    // Toggle selection: if already selected, deselect it by setting to undefined
    if (session.notebook.selectedCell === cell.value) {
        session.notebook.selectedCell = undefined;
    } else {
        session.notebook.selectedCell = cell.value;
    }
};

onMounted(() => {
    // Check if this is a new cell that's already running
    if (queryStatus.value === QueryStatuses.Running && !hasExpandedThoughts.value) {
        expandThoughts();
        hasExpandedThoughts.value = true;
    }
});

const toggleThoughtsVisibility = () => {
    showThoughts.value = !showThoughts.value;
};

const toggleCodeCellForThought = (thoughtIndex: number) => {
    // Instead of deselecting, we'll toggle this thought in the expanded set
    if (expandedThoughts.value.has(thoughtIndex)) {
        expandedThoughts.value.delete(thoughtIndex);
        expandedCodeCells.value.delete(thoughtIndex);
    } else {
        expandedThoughts.value.add(thoughtIndex);
        expandedCodeCells.value.set(thoughtIndex, true); // Default to expanded
        
        // Find the next code_cell event after this thought
        const thoughtEvent = thoughts.value[thoughtIndex];
        const thoughtEventIndex = events.value.findIndex(event => event.id === thoughtEvent.id);
        
        // Look for the next code_cell after this thought
        let nextCodeCell = null;
        for (let i = thoughtEventIndex + 1; i < events.value.length; i++) {
            if (events.value[i].type === 'code_cell') {
                nextCodeCell = events.value[i];
                break;
            }
        }
        
        // Store the related code cell in a map keyed by thought index
        if (nextCodeCell) {
            // We'll modify the template to use this map instead of the single relatedCodeCell ref
            relatedCodeCells.value.set(thoughtIndex, nextCodeCell);
        }
    }
};

// Add this new ref to store related code cells for each thought
const relatedCodeCells = ref<Map<number, BeakerQueryEvent>>(new Map());

const toggleCodeCellExpansion = (event, thoughtIndex: number) => {
    event.stopPropagation(); // Prevent triggering the thought item click
    const currentState = expandedCodeCells.value.get(thoughtIndex) || false;
    expandedCodeCells.value.set(thoughtIndex, !currentState);
};

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
    margin-bottom: 0.5rem;
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

.expand-thoughts-button {
    cursor: pointer;
    border-radius: var(--border-radius);
    margin: 0rem;
    // margin-bottom: 0rem;
    // transition: background-color 0.2s;
    display: block;
    padding: 0.75rem;


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
    gap: 0.5rem;

    &>div {
        flex: 1;
    }

    &>button {
        padding: 0.25rem 0.4rem 0.4rem 0.4rem;
        align-self: center;
        // todo make bg slightly transparent
    }
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

            [data-theme="light"] &:hover {
                background-color: var(--surface-b);
            }

            [data-theme="dark"] &:hover {
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
    // padding-left: 0px;
    padding: 0.5rem;
    background: none;
    border: none;
    // padding-top: 1rem;
    // padding-bottom: 0;
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
    margin-top: 0.5rem;
}

.query-answer-chat-override {
    padding-left: 1rem;
    padding-right: 1rem;
    border-radius: var(--border-radius);
    margin-top: 1rem;
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
    min-width: 22rem;
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

/* Add the sparkles animation */
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

/* New styles for thoughts list */
.thoughts-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 1rem;
}

.thought-item {
  padding: 0.75rem;
  border-radius: var(--border-radius);
  background-color: var(--surface-b);
  cursor: pointer;
  transition: background-color 0.2s;
}

.thought-item:hover {
  background-color: var(--surface-c);
}

.thought-item-selected {
  border-left: 3px solid var(--primary-color);
  background-color: var(--surface-c);
}

.thought-item-alt {
  background-color: #f6f9fc77;
}

.related-code-cell {
  margin-top: 0.75rem;
  padding-top: 0.5rem;
  padding-bottom: 0;
  margin-bottom: 0;
  border-top: 1px dashed var(--surface-border);
  position: relative;
}

.code-cell-controls {
  display: flex;
  justify-content: center;
  margin: 0;
//   margin-bottom: 0.5rem;
  padding: 0;
  position: absolute;
  top: -2.65rem;
  right: 3rem;
  // inset-inline-end: 50%;
}

.code-cell-toggle-button {
//   background-color: purple;
  // color: purple;
  margin: 0;
}

.code-cell-collapsed {
  max-height: 200px;
  overflow-y: hidden;
  border: 1px solid var(--surface-border);
  border-radius: var(--border-radius);
}

.agent-actions-header {
  cursor: pointer;
  user-select: none;
}

.agent-actions-toggle {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.5rem;
}

.agent-actions-toggle i {
  margin-left: 0.5rem;
}

.agent-actions-header:hover {
  opacity: 0.8;
}

.agent-actions-toggle-text {
  font-size: 1rem;
}

</style>
