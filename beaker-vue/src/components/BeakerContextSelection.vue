<template>

    <Dialog
        v-model:visible="contextDialogOpen"
        :closable="false"
        modal
        header="Configure Context"
        :style="{ width: '30rem' }"
    >
        <InputGroup>
            <Dropdown
                v-model="selectedContextSlug"
                :options="contextOptions"
                optionLabel="slug"
                optionValue="slug"
            />

            <Dropdown
                v-model="selectedLanguage"
                :options="languageOptions"
                optionLabel="slug"
                optionValue="subkernel"
            />
        </InputGroup>

        <br />

        <Codemirror
            :tab-size="2"
            language="javascript"
            v-model="contextPayload"
        />

        <div style="width: 100%; margin: auto; text-align: center; margin-top: 1rem;">
            <Button @click="setContext" size="small">Get Started</Button>
        </div>

    </Dialog>
</template>

<script setup lang="ts">

import { defineProps, defineEmits, ref, defineModel, onMounted, computed, nextTick, onBeforeMount, watchEffect } from "vue";
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import InputGroup from 'primevue/inputgroup';
import Dropdown from 'primevue/dropdown';
import { Codemirror } from "vue-codemirror";

const props = defineProps([
    "session",
    "contextData",
]);

const contextDialogOpen = ref(true);

const contextData = ref(undefined);

const emit = defineEmits([
    "select-cell",
    "run-cell",
    "update-context-info",
]);

const selectedContextSlug = ref<string>();
const selectedLanguage = ref<string | undefined>(undefined);
const contextPayload = ref<string | undefined>(undefined);

interface IBeakerContext {
    languages: {
        slug: string,
        kernel: string,
    }[],
    defaultPayload: string,
}

const contextOptions = computed(() => {
    const availableOptions = Object.keys(contextData.value || {});

    if (Array.isArray(availableOptions)) {
        return availableOptions.map(s => ({slug: s}))
    }

    return [];
});

const selectedContext = computed<IBeakerContext | undefined>(() => {
    if (contextData.value !== undefined && selectedContextSlug.value) {
        return contextData.value[selectedContextSlug.value];
    }
    else {
        return undefined;
    }
});
const languageOptions = computed<{slug: string, kernel: string}[]>(() => {
    if (!contextData.value || selectedContext.value === undefined) {
        return [];
    }
    return selectedContext.value.languages;
});

watchEffect(() => {
    if (
        props.contextData?.language.subkernel
        && selectedLanguage.value === undefined
    ) {
        selectedLanguage.value = props.contextData.language.subkernel;
    }
    else if (selectedContext.value && selectedContext.value.languages.map<string|undefined>((item) => item.subkernel).indexOf(selectedLanguage.value) === -1) {
        selectedLanguage.value = selectedContext.value?.languages[0].subkernel;
    }
});

watchEffect(() => {
    contextPayload.value = selectedContext.value?.defaultPayload;
});

const setContext = () => {
    const future = props.session.sendBeakerMessage(
        "context_setup_request",
    {
      context: selectedContextSlug.value,
      language: selectedLanguage.value,
      context_info: JSON.parse(contextPayload.value || ''),
    }
    );
    future.done.then(() => {
        emit("update-context-info");
        contextDialogOpen.value = false; 
    });
}

onMounted(async () => {
    const contexts = await props.session.availableContexts();
    contextData.value = contexts;
    selectedContextSlug.value = Object.keys(contexts)[0];
})
</script>


<style>
.context-selection-container {
    height: 0px;
    overflow: hidden;
    transition: all 0s;
    display: hidden;
}

</style>
