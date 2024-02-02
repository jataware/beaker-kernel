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
                        <Button outlined label="Save" size="small" @click="saveEdit"/>
                        <Button outlined severity="danger" @click="cancelEdit" label="Cancel" size="small" />
                    </div>
                </div>
                <div v-else>
                    <span v-if="savedEdit">
                        {{savedEdit}}
                    </span>
                    <span v-else>
                        {{ cell.source }}
                    </span>
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
                    v-if="busy"
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
        <div class="thought" v-for="thought of cell.thoughts" :key="thought">Thought: {{ thought }}</div>
        <div class="response">{{ cell.response }}</div>
    </div>

</template>

<script setup lang="ts">
import { defineProps, ref, computed, nextTick } from "vue";
import Button from "primevue/button"; 
import InputText from 'primevue/inputtext';

// TODO put actions in a card/container?

const props = defineProps([
    "cell",
    "session",
]);

const cell = ref(props.cell);
const timeout = ref(false);
const editing = ref(false);
const editingContents = ref("");
const autofocus = ref();
const savedEdit = ref("");


setTimeout(() => {
    timeout.value = true;
}, 8000);

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
}

const busy = computed(() => {
    return props.cell.source &&
     !props.cell.response &&
     !timeout.value
});

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


</style>
