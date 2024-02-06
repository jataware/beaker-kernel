<template>

    <Dialog
        v-bind:visible="props.isOpen"
        @update:visible="closeDialog"
        closable
        modal
        header="Configure Context"
        :style="{ width: '40rem' }"
    >
        <p>
            Select kernel and language.
        </p>
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

        <h4 class="h-less-pad">Context Info</h4>

        <div class="code-container">
            <Codemirror
                :extensions="codeExtensions"
                :tab-size="2"
                language="javascript"
                v-model="contextPayload"
            />
        </div>

        <div>
            <h4 class="h-less-pad">Logging</h4>
            <div class="flex" style="align-items: center;">
                <div class="labeled-check">
                    <Checkbox v-model="logDebug" inputId="logging-debug-check" value="true" />
                    <label for="logging-debug-check" class="ml-1">Debug</label>
                </div>
                <div class="labeled-check ml-2">
                    <Checkbox v-model="logVerbose" inputId="logging-verbose-check" value="true" />
                    <label for="logging-verbose-check" class="ml-1">Verbose</label>
                </div>
            </div>
        </div>

        <template #footer>
            <div style="width: 100%; text-align: center;">
                <Button
                    raised
                    @click="setContext"
                    label="Save"
                    size="small"
                />
            </div>
        </template>

    </Dialog>
</template>

<script setup lang="ts">

import { defineProps, defineEmits, ref, onMounted, computed, watchEffect } from "vue";
import { Codemirror } from "vue-codemirror";
import { oneDark } from '@codemirror/theme-one-dark';
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import InputGroup from 'primevue/inputgroup';
import Dropdown from 'primevue/dropdown';
import Checkbox from 'primevue/checkbox';

const props = defineProps([
    "session",
    "activeContext",
    "isOpen",
    "toggleOpen",
    "theme"
]);

const contextData = ref(undefined);
const logDebug = ref(false);
const logVerbose = ref(false);

const closeDialog = () => {
    props.toggleOpen();
    logDebug.value = false;
    logVerbose.value = false;
}

const emit = defineEmits([
    "select-cell",
    "run-cell",
    "update-context-info",
]);

const selectedContextSlug = ref<string>();
const selectedLanguage = ref<string | undefined>(undefined);
const contextPayload = ref<string | undefined>(undefined);


const codeExtensions = computed(() => {
    const ext = [];

    if (props.theme === 'dark') {
        ext.push(oneDark);
    }
    return ext;

});

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
        props.activeContext?.language.subkernel
        && selectedLanguage.value === undefined
    ) {
        selectedLanguage.value = props.activeContext.language.subkernel;
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
      debug: Boolean(logDebug.value[0]),
      verbose: Boolean(logVerbose.value[0]),
    }
    );
    future.done.then(() => {
        emit("update-context-info");
        sessionStorage.setItem('active_context', selectedContextSlug.value);
        sessionStorage.setItem('kernel_language', selectedLanguage.value);
        sessionStorage.setItem('context_info', contextPayload.value);
        props.toggleOpen();
    });
}

onMounted(async () => {
    const contexts = await props.session.availableContexts();
    contextData.value = contexts;

    const savedContext = sessionStorage.getItem('active_context');

    if (savedContext) {
        selectedContextSlug.value = savedContext;
        return;
    }
    selectedContextSlug.value = Object.keys(contexts)[0];
})
</script>


<style lang="scss">
.labeled-check {
    display: flex;
    align-items: center;
}

.ml-2 {
    margin-left: 1rem;
}

.ml-1 {
    margin-left: 0.25rem;
}

.flex {
    display: flex;
}

.h-less-pad {
    margin-block-end: 1rem;   
}

.code-container {
    border: 1px solid var(--surface-ground);
    padding: 0.25rem;    
    max-height: 15rem;
    overflow: auto;
}

.p-dialog-header {
    background-image: linear-gradient(45deg, var(--surface-a), var(--surface-a), var(--surface-a), var(--surface-b), var(--surface-b), var(--surface-b));
}

</style>
