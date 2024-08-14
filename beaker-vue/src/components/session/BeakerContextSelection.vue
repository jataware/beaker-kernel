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
            Select context and language.
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
            <CodeEditor
                :tab-size="2"
                language="javascript"
                v-model="contextPayloadData[selectedContextSlug]"
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
                    :loading="props.contextProcessing"
                    raised
                    @click="setContext"
                    label="Apply"
                    size="small"
                />
            </div>
        </template>

    </Dialog>
</template>

<script setup lang="ts">

import { defineProps, defineEmits, ref, onMounted, computed, watch, inject } from "vue";
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import InputGroup from 'primevue/inputgroup';
import Dropdown from 'primevue/dropdown';
import Checkbox from 'primevue/checkbox';
import { BeakerSessionComponentType } from './BeakerSession.vue';
import CodeEditor from '../misc/CodeEditor.vue';

const props = defineProps([
    "isOpen",
    "contextProcessing"
]);

const contextData = ref(undefined);
const logDebug = ref([]);
const logVerbose = ref([]);
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");

const emit = defineEmits([
    "update-context-info",
    "context-changed",
    "close-context-selection",
]);

const selectedContextSlug = ref<string>();
const selectedLanguage = ref<string | undefined>(undefined);
const contextPayloadData = ref({});


const closeDialog = () => {
    emit("close-context-selection")
};


interface IBeakerContext {
    languages: {
        slug: string,
        kernel: string,
        subkernel: string,
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
const languageOptions = computed<{slug: string, kernel: string, subkernel: string}[]>(() => {
    if (!contextData.value || selectedContext.value === undefined) {
        return [];
    }
    return selectedContext.value.languages;
});

// When selectedContextSlug dropdown changes, the selected
// language might not be available in the new languageOptions/context
// Ensure to default the selected language for that context to 1st option available
watch(selectedContextSlug, (newSelectedContextSlug: string) => {
    const langOpts = languageOptions.value;
    const currentLanguage = selectedLanguage.value;

    if(!currentLanguage) {
        return;
    }

    if (Array.isArray(langOpts) && langOpts.length) {
        const isSelectedAvailable = langOpts
           .map(i => i.subkernel)
           .includes(currentLanguage);

        if (!isSelectedAvailable) {
            selectedLanguage.value = langOpts[0].subkernel;
        }


        // When changing from active context slug to a different one, set default payload
        // if user has not modified it before (payload data is still empty)
        const existingContextPayload = contextPayloadData.value[newSelectedContextSlug];

        if (!existingContextPayload) {
            contextPayloadData.value[newSelectedContextSlug] = contextData.value[selectedContextSlug.value].defaultPayload;
        }
    }
});

// TODO clean this once we understand how checkboxes state work..
watch(() => props.isOpen, (open /*, oldValue*/) => {

    // Only setup saved context state when opening the dialog (not closing).
    if (open) {

        if (beakerSession.activeContext.language) {
            // Panel just opened and activeContext data available:
            selectedLanguage.value = beakerSession.activeContext.language.subkernel;
            selectedContextSlug.value = beakerSession.activeContext.slug;

            // First time we open, if payload empty, load from active context
            const existingContextPayload = contextPayloadData.value[selectedContextSlug.value];
            if (!existingContextPayload) {
                contextPayloadData.value[selectedContextSlug.value] = JSON.stringify(beakerSession.activeContext.config);
            }
        }

        if (beakerSession.activeContext.info) {
        // Panel just opened and activeContext info available (verbose/debug checks)
            const strDebugValue = beakerSession.activeContext.info.debug.toString();

            if (logDebug.value.length) {
                logDebug.value[0] = strDebugValue;
            } else {
                logDebug.value.push(strDebugValue);
            }
            const strVerboseValue = beakerSession.activeContext.info.verbose.toString();

            if (logVerbose.value.length) {
                logVerbose.value[0] = strVerboseValue;
            } else {
                logVerbose.value.push(strVerboseValue);
            }

        }
    }
});

const setContext = async () => {
    // TODO determine if there's a better way to work with primevue's checkbox state
    const isDebug = logDebug.value.includes('true');
    const isVerbose = logVerbose.value.includes('true');

    const contextInfo = contextPayloadData.value[selectedContextSlug.value];

    const contextMessageContent = {
      context: selectedContextSlug.value,
      language: selectedLanguage.value,
      context_info: JSON.parse(contextInfo || ''),
      debug: isDebug,
      verbose: isVerbose,
    };
    emit("context-changed", contextMessageContent);
    emit("close-context-selection")
}

/*
 Sample context shape:
 TODO type interface
{
    decapodes: {
        defaultPayload: "{}",
        languages: [{slug: 'julia', subkernel: 'julia2'}]
    }
}
*/
onMounted(async () => {
    const contexts = await beakerSession?.session?.availableContexts();
    if(contexts) {
        contextData.value = contexts;
        selectedContextSlug.value = Object.keys(contexts)[0];
    }
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
