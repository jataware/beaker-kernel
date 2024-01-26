<template>
    <div :class="{'context-selection-container': true, 'expanded': props.expanded}">
        <div>
            <select class="context-name" v-model="selectedContextSlug">
                <option v-for="contextName of Object.keys(contextData || {})" :value="contextName" :label="contextName" :key="contextName"></option>
            </select>
            <select v-model="selectedLanguage">
                <option v-for="{slug, subkernel} of languageOptions" :value="subkernel" :label="slug" :key="subkernel"></option>
            </select>
            <!-- <textarea class="json-input" v-model="contextPayload"></textarea> -->
            <div class="message-content-container">
                <Codemirror
                    :tab-size="2"
                    language="javascript"
                    v-model="contextPayload"
                />
            </div>
            <button @click="setContext">Submit</button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, ref, defineModel, onMounted, computed, nextTick, onBeforeMount, watchEffect } from "vue";
import { Codemirror } from "vue-codemirror";

const props = defineProps([
    "session",
    "contextData",
    "expanded",
]);

const contextData = ref(undefined);

const query = ref("");
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

// const selectedContext = computed<{languages: [string, string][], defaultPayload: string} | undefined>(() => {
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
    /* padding: 0.5em; */
    height: 0px;
    overflow: hidden;
    /* min-height: 300px; */
    /* margin-top: -100%; */
    transition: all 0s;
    display: hidden;
}

.context-selection-container.expanded {
    border: 1px solid darkgray;
    height: auto;
    padding: 0.5em;
    display: block;
}



</style>
