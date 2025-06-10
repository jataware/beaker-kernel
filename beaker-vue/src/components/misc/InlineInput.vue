<template>
        <Inplace
            ref="inPlaceRef"
            v-model:active="editorActive"
            @open="editorModel = model"
        >
            <template #display>
                <InputGroup>
                    <InputGroupAddon style="flex: 1;">
                        <span style="font-weight: bold;">{{ model }}</span>
                    </InputGroupAddon>
                    <Button icon="pi pi-pencil"/>
                </InputGroup>
            </template>
            <template #content>
            <InputGroup>
                <InputText
                    ref="inputTextRef"
                    v-model:model-value="editorModel"
                    autofocus
                    :original-value="new String(toRaw(model))"
                    @keydown.enter="saveChanges"
                    @keydown.escape="rejectChanges"
                />
                <Button icon="pi pi-check" severity="success"
                    @click="saveChanges"
                />
                <Button icon="pi pi-times" severity="warning"
                    @click="rejectChanges"
                />
                </InputGroup>
            </template>
        </Inplace>

</template>

<script setup lang="ts">
import { ref, toRaw } from 'vue';
import Inplace from 'primevue/inplace';
import InputGroup from 'primevue/inputgroup';
import InputGroupAddon from 'primevue/inputgroupaddon';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';

const model = defineModel<string>();
const editorModel = ref<string>(model.value || "");
const inPlaceRef = ref();
const inputTextRef = ref();
const editorActive = ref<boolean>(false);

const saveChanges = () => {
    if (editorModel.value !== model.value) {
        model.value = editorModel.value;
    }
    editorActive.value = false;
}

const rejectChanges = () => {
    editorActive.value = false;
    editorModel.value = model.value;
}

</script>
