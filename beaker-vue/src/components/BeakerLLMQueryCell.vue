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
                    <div>
                        {{ cell.source }} <span v-if="savedEdit" style="font-weight: 100;">(edited)</span>
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
        <div class="events" :class="event.type" v-for="event of events" :key="event">
            <span v-if="event.type === 'thought'">Thought:&nbsp;</span>
            <template v-if="event.type === 'thought'" >{{ event.content }}</template>
            <span v-if="event.type ==='code_cell'">
                <Component
                    v-if="typeof(getChildByCellId(event.content?.id)) !== 'undefined'"
                    
                    :key="event.content.id"
                    :is="BeakerCodeCell"
                    :cell="getChildByCellId(event.content.id)"
                    :index="`${index}:${event.content.index}`"
                    :class="{
                        selected: (index === selectedCellIndex)
                    }"
                    ref="childrenRef"
                    drag-enabled=false
                    @click.stop="props.childOnClickCallback(`${index}:${event.content.index}`)"
                />
            </span>
            <template v-if="event.type === 'response'" >{{ event.content }}</template>
            <template v-if="event.type === 'abort'" >{{ event.content }}</template>
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
import { defineProps, defineExpose, ref, nextTick, inject } from "vue";
import Button from "primevue/button";
import ContainedTextArea from './ContainedTextArea.vue';
import { IIOPubMessage } from "@jupyterlab/services/lib/kernel/messages";
import { BeakerBaseCell, BeakerSession } from 'beaker-kernel';
import BeakerCodeCell from './BeakerCodecell.vue';

const props = defineProps([
    'index',
    'cell',
    'selectedCellIndex',
    'childOnClickCallback',
    'selectNext',
    'excludedEvents'
]);

const cell = ref(props.cell);
const editing = ref(false);
const editingContents = ref("");
const savedEdit = ref("");
const response = ref("");
const session: BeakerSession = inject("session");
const childrenRef = ref<typeof BeakerCodeCell|null>(null);
const events = props.cell.events.filter(({ type }) => !(props.eventFilter || ["thought"]).includes(type));

const getChildByCellId = (child_id: string) : BeakerBaseCell | undefined => {
    const index = cell.value.children?.findIndex((child) => child.id === child_id)
    return cell.value?.children?.[index]
}

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
    padding: 0.5rem 0.35rem 1rem 1.2rem;
}

.query-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.events {
    padding: 0.25rem 0;
}

.query {
    font-weight: bold;
    flex: 1;
    line-height: 2.5rem;
    margin-bottom: 0.25rem;
}

.user_question {
    font-style: italic;
}

.user_answer {
    border-radius: 4px;
    background-color: var(--surface-c);
    padding: 0.4rem;
    display: inline-block;
    margin: 0.2rem 0;
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

</style>
