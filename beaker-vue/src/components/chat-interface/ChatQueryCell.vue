<template>
    <BaseQueryCell>
    <template #query>
        <div
            class="query query-chat"
            @dblclick="promptDoubleClick"
        >
            <!-- render user question and user response -->
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
    </template>
    <template #events>
        <div class="event-container"
            v-if="events.length > 0 || isLastEventTerminal(events) || showChatEventsEarly(cell)"
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
                <!-- render agent question to user and any user responses -->
                <div v-for="[messageEvent, messageClass] of messageEvents" v-bind:key="messageEvent.id">
                    <div style="display: flex; flex-direction: column;">
                        <BeakerQueryCellEvent
                            :event="messageEvent"
                            :parent-query-cell="cell"
                            :class="messageClass"
                        />
                    </div>
                </div>
                <!-- Show final agent response/answer to original query -->
                <div 
                    class="query-answer-chat-override"
                    v-if="isLastEventTerminal(events)"
                >
                    <BeakerQueryCellEvent
                        :event="cell?.events[cell?.events.length - 1]"
                        :parent-query-cell="cell"
                    />
                </div>
            </div>
        </div>
    </template>
    <template #input-request>
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
    </template>
  </BaseQueryCell>

</template>

<script setup lang="ts">
import { defineProps, defineExpose, ref, shallowRef, inject, computed, nextTick, onBeforeMount, getCurrentInstance, onBeforeUnmount, watch, toRaw } from "vue";
import Button from "primevue/button";
import InputGroup from 'primevue/inputgroup';
import InputText from 'primevue/inputtext';
import InputGroupAddon from 'primevue/inputgroupaddon';
import { BeakerSession } from 'beaker-kernel/src';
import BeakerQueryCellEvent from "../cell/BeakerQueryCellEvent.vue";
import ContainedTextArea from '../misc/ContainedTextArea.vue';
import { BeakerSessionComponentType } from "../session/BeakerSession.vue";
import { isLastEventTerminal } from "../cell/cellOperations";
import { useBaseQueryCell } from '../cell/BaseQueryCell';
import BaseQueryCell from '../cell/BaseQueryCell.vue';

const props = defineProps([
    'index',
    'cell',
]);

const {
  cell,
  isEditing,
  promptEditorMinHeight,
  promptText,
  response,
  textarea,
  events,
  execute,
  enter,
  exit,
  clear,
  respond
} = useBaseQueryCell(props);

const enum QueryStatuses {
    NotExecuted,
    Running,
    Done,
}

const session: BeakerSession = inject("session");
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
const instance = getCurrentInstance();

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
    const previousSelectedCell = session.notebook.selectedCell;
    if (previousSelectedCell === cell.value) {
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
    else if (isLastEventTerminal(events.value)) {
        return QueryStatuses.Done;
    }
    else {
        return QueryStatuses.Running;
    }
})

// Auto-select cell thoughts when we first start getting events
// and auto-close when the agent is done, in which case the user can see the final response
// on the chat history. User can always manually expand the thoughts to examine what occured before if they want to.
watch(events, (newEvents) => {
    const startedRunning = queryStatus.value === QueryStatuses.Running && newEvents.length === 1;
    if (startedRunning) {
        expandThoughts();
    }
});
watch(queryStatus, (newStatus) => {
    if (newStatus === QueryStatuses.Done) {
        session.notebook.selectedCell = undefined;
    }
});


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

const promptDoubleClick = (event) => {
    if (!isEditing.value) {
        promptEditorMinHeight.value = (event.target as HTMLElement).clientHeight;
        isEditing.value = true;
    }
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