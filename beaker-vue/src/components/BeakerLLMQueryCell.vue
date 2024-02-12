<template>
    <div class="llm-query-cell">
        <div class="query-row">
            <div class="query">
                <div v-if="editing" style="display: flex">
                    <InputText
                        type="text"
                        size="small"
                        ref="autofocus"
                        v-model="editingContents"
                    />
                    <div class="edit-actions">
                        <Button outlined class="save-button" label="Save" size="small" @click="saveEdit"/>
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
        <div :class="event.type" v-for="event of cell.events" :key="event">
            <span v-if="event.type === 'thought'">Thought:&nbsp;</span>{{ event.content }} 
            <div v-if="cell.status === 'awaiting_input'">
                <InputText v-model="response"></InputText><Button label="Respond" @click="respond">Respond</Button>
            </div>
        </div>
    </div>

</template>

<script setup lang="ts">
import { defineProps, ref, computed, nextTick } from "vue";
import Button from "primevue/button";
import InputText from 'primevue/inputtext';


const props = defineProps([
    "cell",
    "session",
]);

const cell = ref(props.cell);
const editing = ref(false);
const editingContents = ref("");
const autofocus = ref();
const savedEdit = ref("");
const response = ref("");


function cancelEdit() {
    editing.value = false;
    editingContents.value = savedEdit.value || cell.value.source;
}

async function startEdit() {
    if (editing.value === true) {
        await nextTick();
        autofocus.value.$el.focus();
        return;
    }
    editing.value = true;
    editingContents.value = savedEdit.value || cell.value.source;
    await nextTick();
    autofocus.value.$el.focus();
}

function saveEdit() {
    editing.value = false;
    savedEdit.value = editingContents.value;
    cell.value.source = editingContents.value;
}


const respond = () => {
    props.cell.respond(response.value, props.session);

};

</script>


<style lang="scss">
.llm-query-cell {
    padding: 0.5rem 1.2rem 1rem 1.2rem;
}

.query-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.query {
    font-weight: bold;
    flex: 1;
    line-height: 2.5rem;
    margin-bottom: 0.5rem;
}

.user_question {
    font-style: italic;
}

.user_answer {
    
}

.thought {
    color: var(--blue-400);
}

.response {
    margin-top: 1em;
    white-space: pre-line;
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
    margin-left: 0.5rem;
    .p-button {
        margin-right: 0.5rem;
    }
}

.save-button {
    border-color: var(--surface-200);
    color: var(--primary-text-color);
}

.cancel-button {
    border-color: var(--surface-100);
    color: var(--primary-text-color);
}

</style>
