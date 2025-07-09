<template>
    <div class="integration-editor">
        <div class="integration-loading" v-if="beakerSession.status === 'connecting'">
            <ProgressSpinner></ProgressSpinner>
            Loading integrations...
            {{beakerSession?.status}}
        </div>
        <div class="integration-main-content" v-else>
            <div class="integration-header">
                <Select :options="
                    sortedIntegrations.map(integration => ({
                        label: integration.name,
                        value: integration.slug
                    }))"
                    :option-label="(option) => option?.label ?? 'Select integration...'"
                    option-value="value"
                    placeholder="Select a integration..."
                    @click="(event) => {
                        if (!confirmUnsavedChanges()) {
                            event.preventDefault;
                        } else {
                            model.unsavedChanges = false;
                        }
                    }"
                    v-model="model.selected">
                </Select>

                <SplitButton
                    @click="() => {
                        if (confirmUnsavedChanges()) {
                            newIntegration();
                        }
                    }"
                    label="New API Integration"
                    :model="[
                        {
                            label: 'New API Integration',
                            command: () => {}
                        },
                        {
                            label: 'New Dataset Integration',
                            command: () => {}
                        }
                    ]"
                >
                </SplitButton>
            </div>

            <Fieldset legend="Name">
                <InputText
                    v-if="selectedIntegration"
                    v-model="selectedIntegration.name"
                    :placeholder="selectedIntegration?.name ? 'Name' : 'No integration selected.'"
                    @change="model.unsavedChanges = true;"
                />
                <InputText
                    v-else
                    disabled
                    placeholder="No integration selected."
                />
            </Fieldset>

            <Fieldset legend="Description">
                <p>
                    The description, used by both users and the agent, provides a brief summary of the purpose of this
                    integration. The agent will use this to select which integration best matches a user's request.
                </p>
                <div class="constrained-editor-height">
                    <CodeEditor
                        v-if="selectedIntegration"
                        v-model="selectedIntegration.description"
                        @change="model.unsavedChanges = true"
                        ref="descriptionEditor"
                    />
                    <CodeEditor
                        v-else
                        disabled
                        v-model="emptyText"
                        placeholder="No integration selected."
                    />
                </div>
            </Fieldset>

            <Fieldset legend="User Files">
                <p>
                    Uploaded files will be used by the agent in one of two ways: either included in the instruction body,
                    or when running code based on a user's request. For included documentation, these files should
                    be included in the body and will be used in determining what steps to take for the user's request.
                    For large datasets, these are used once the agent is executing a request.
                </p>
                <form ref="uploadForm">
                    <input
                        @change="onSelectFileForUpload"
                        ref="fileInput"
                        type="file"
                        style="display:none;"
                        name="uploadfiles"
                    />
                    <input
                        type="hidden"
                        name="_xsrf"
                        :value="xsrfCookie"
                    />
                </form>
                <form ref="uploadFormMultiple">
                    <input
                        @change="onSelectFilesForUpload"
                        ref="fileInputMultiple"
                        type="file"
                        style="display:none;"
                        name="uploadfilesMultiple"
                        multiple
                    />
                    <input
                        type="hidden"
                        name="_xsrf"
                        :value="xsrfCookie"
                    />
                </form>
                <Toolbar v-for="file, id in attachedFiles" :key="file?.filepath">
                    <template #start>
                        <Button
                            icon="pi pi-download"
                            v-tooltip="'Download'"
                            style="width: 32px; height: 32px"
                            @click="downloadFile(id)"
                        />
                    </template>
                    <template #center>
                        <InputText v-model="file.name" type="text"></InputText>
                    </template>
                    <template #end>
                        <Button
                            icon="pi pi-trash"
                            severity="danger"
                            style="width: 32px; height: 32px"
                            @click="removeFile(id)"
                            v-tooltip="'Remove File'"
                        />
                    </template>
                </Toolbar>
                <Button
                    @click="openFileSelectionMultiple"
                    style="width: fit-content; height: 32px;"
                    label="Add New Files"
                    icon="pi pi-plus"
                    :disabled="!selectedIntegration"
                />
            </Fieldset>

            <div
                style="display: flex;
                flex-direction: column;
                gap: 0.5rem"
                v-if="unincludedFiles.length > 0"
            >
                <Tag
                    icon="pi pi-exclamation-triangle"
                    severity="warning"
                    size="large"
                >
                    Some files are not included: {{ unincludedFiles.join(', ') }}; see the above documentation about how to reference these files.
                </Tag>
            </div>

            <Fieldset legend="Agent Instructions">
                <p>
                    Agent instructions will be given to the agent when it creates a plan to execute a user's request.
                </p>
                <span style="margin-bottom: 1rem">
                    Files uploaded above can be referenced in the below agent instructions with
                    <span style="font-family: monospace;">{filename}</span>,
                    such as if you uploaded a file named
                    <span style="font-family: monospace;">documentation.txt</span>
                    and it shows above with the name
                    <span style="font-family: monospace;">documentation</span>,
                    adding
                    <span style="font-family: monospace;">{documentation}</span> to the body below will ensure the agent
                    can read your uploaded file.
                </span>
                <div class="constrained-editor-height">
                    <CodeEditor
                        v-if="selectedIntegration"
                        v-model="selectedIntegration.source"
                        @change="model.unsavedChanges = true"
                        ref="instructionEditor"
                    />
                    <CodeEditor
                        v-else
                        disabled
                        v-model="emptyText"
                        placeholder="No integration selected."
                    />
                </div>
            </Fieldset>
        </div>
        <div style="flex: 1 0; margin: 0.2rem; display: flex; justify-content: flex-end;">
            <div v-if="model.unsavedChanges" style="flex-shrink: 0;">
                <Button
                    @click="save"
                    :disabled="!selectedIntegration"
                    icon="pi pi-save"
                    label="Save Changes"
                    severity="success"
                />
            </div>
        </div>
    </div>
</template>


<script setup lang="ts">

import { defineProps, ref, watch, computed, nextTick, inject, defineModel } from 'vue';
import { type IntegrationMap, type Integration, getIntegrationProviderType, type IntegrationAttachedFile, type IntegrationResourceMap, type IntegrationInterfaceState, filterByResourceType, postIntegration, postResource, deleteResource } from '../../util/integration';
import { BeakerSession } from 'beaker-kernel';
import type { BeakerSessionComponentType } from '../session/BeakerSession.vue';

import Select from 'primevue/select';
import Fieldset from 'primevue/fieldset';
import Button from "primevue/button";
import Divider from 'primevue/divider';
import Toolbar from 'primevue/toolbar';
import InputText from 'primevue/inputtext';
import ProgressSpinner from 'primevue/progressspinner';
import Tag from 'primevue/tag';

import * as cookie from 'cookie';

import { ContentsManager, Contents } from '@jupyterlab/services';
import CodeEditor from './CodeEditor.vue';
import SplitButton from 'primevue/splitbutton';

import { v4 as uuidv4 } from "uuid";

import { useRoute } from 'vue-router';

const showToast = inject<any>('show_toast');

const props = defineProps<{
    selectedOnLoad: string,
    sessionId: string,
}>();

const beakerSession = inject<BeakerSessionComponentType>("beakerSession");

const model = defineModel<IntegrationInterfaceState>()

const hasLoadedInitialSelection = ref(false);

const emit = defineEmits(['refresh'])

const sortIntegrations = (integrations: IntegrationMap): Integration[] =>
    Object.values(integrations).toSorted((a, b) => a?.name.localeCompare(b?.name))

const adhocIntegrations = computed<IntegrationMap>(() =>
    Object.fromEntries(Object.entries(model.value.integrations ?? {})
        .filter(([_name, integration]) => getIntegrationProviderType(integration) === "adhoc")))

const sortedIntegrations = computed<Integration[]>(() => sortIntegrations(adhocIntegrations.value))

const selectedIntegration = computed<Integration>(() => adhocIntegrations.value[model.value.selected])

const attachedFiles = computed<{[key in string]: IntegrationAttachedFile}>(() =>
    filterByResourceType<IntegrationAttachedFile>(
        model.value.integrations[model.value.selected]?.resources, "file")
    )

const uncommittedDeletedResources = ref([]);

watch(() => model.value.selected, () => {
    // always pull from backend when changing selected -- except for a brand new integration that won't have been committed yet
    if (model?.value?.integrations[model?.value?.selected]?.name === "New Integration") {
        return;
    }
    else {
        uncommittedDeletedResources.value = [];
        emit("refresh");
    }
})

const route = useRoute();
// in the case of non-remounting, where ?selected= is changed via other means, go with that
watch(() => route, (newRoute) => {
    model.value.selected = newRoute.query?.selected as string|undefined ?? model.value.selected;
}, {immediate: true, deep: true})

watch(model, ({integrations, unsavedChanges}) => {
    if (unsavedChanges) {
        onbeforeunload = () => true;
    } else {
        onbeforeunload = undefined;
    }

    if (Object.keys(integrations).length === 0) {
        return;
    }
    if (hasLoadedInitialSelection.value) {
        return;
    }
    if (props?.selectedOnLoad) {
        nextTick(() => {
            if (props?.selectedOnLoad === 'new') {
                newIntegration();
            }
            else {
                model.value.selected = props.selectedOnLoad;
            }
        })
    }
    hasLoadedInitialSelection.value = true;
})

const descriptionEditor = ref();
watch(() => [selectedIntegration?.value?.description], (current) => {
    if (descriptionEditor.value) {
        descriptionEditor.value.model = current[0];
    }
})

const instructionEditor = ref();
watch(() => [selectedIntegration.value?.source], (current) => {
    if (instructionEditor.value) {
        instructionEditor.value.model = current[0];
    }
})

const emptyText = ref<string|undefined>(undefined);

const fileInput = ref<HTMLInputElement|undefined>(undefined);
const fileInputMultiple = ref<HTMLInputElement|undefined>(undefined);
const uploadForm = ref<HTMLFormElement|undefined>(undefined);
const uploadFormMultiple = ref<HTMLFormElement|undefined>(undefined);

const unincludedFiles = computed<[string, IntegrationAttachedFile][]>(() => {
    let unincluded = [];
    for (const file of Object.values(attachedFiles.value)) {
        // [$] is an alternative to backslash escaping
        // we want to match python's ${interpolation_key} -- where file.name is the interpolation key
        const pattern = RegExp(`[$]{${file?.name}}`);
        if (!pattern.test(selectedIntegration?.value?.source)) {
            unincluded.push(file.name);
        }
    }
    return unincluded;
})

const confirmUnsavedChanges = () => {
    if (model.value.unsavedChanges) {
        return confirm("You currently have unsaved changes that would be lost with this change. Are you sure?")
    }
    return true;
}

const removeFile = async (id) => {
    model.value.unsavedChanges = true;
    delete selectedIntegration.value.resources[id];
    // if exists remote -- if it's only a local unsaved change, the request here is a no-op
    uncommittedDeletedResources.value.push(id);
}

const fileTarget = ref();

const openFileSelection = (target) => {
    fileTarget.value = target;
    fileInput.value?.click();
}

const openFileSelectionMultiple = () => {
    fileTarget.value = undefined;
    fileInputMultiple.value?.click();
}

const cookies = cookie.parse(document.cookie);
const xsrfCookie = cookies._xsrf;

const newIntegration = () => {
    const uuid = uuidv4()
    const integration: Integration = {
        name: "New Integration",
        url: "",
        slug: uuid,
        source: "This is the prompt information that the agent will consult when using the integration. Include API details or how to find datasets here.",
        description: "This is the description that the agent will use to determine when this integration should be used.",
        provider: "adhoc:specialist_agents"
    }
    model.value.integrations[uuid] = integration;
    model.value.selected = uuid;
    model.value.unsavedChanges = true;
}

const save = async () => {
    if (selectedIntegration?.value === undefined) {
        return;
    }

    for (const [file_id, file] of Object.entries(attachedFiles.value)) {
        console.log(await postResource({
            sessionId: props.sessionId,
            integrationId: model.value.selected,
            resourceId: file_id,
            body: file
        }))
    }
    for (const id of uncommittedDeletedResources.value) {
        await deleteResource(props.sessionId, model.value.selected, id);
    }
    await postIntegration(props.sessionId, model.value.selected, selectedIntegration.value);

    showToast({
        title: 'Saved!',
        detail: `The session will now reconnect and load the new definition.`,
        severity: 'success',
        life: 4000
    });
    emit("refresh");

    model.value.unsavedChanges = false;
}

const onSelectFileForUpload = async () => {
    const fileList = uploadForm.value['uploadfiles']?.files;
    await uploadFile(fileList);
}

const onSelectFilesForUpload = async () => {
    const fileList = uploadFormMultiple.value['uploadfilesMultiple']?.files;
    await uploadFile(fileList);
}

const uploadFile = async (files: FileList) => {
    model.value.unsavedChanges = true;
    const promises = Array.from(files).map(async (file) => {
        const bytes = [];
        const reader = file.stream().getReader();
        var chunk = (await reader.read()).value;
        while (chunk?.length > 0) {
            bytes.push(Array.from(chunk, (byte) => String.fromCharCode(byte)).join(""));
            chunk = (await reader.read()).value;
        }
        const uuid = uuidv4();
        const fileResource: IntegrationAttachedFile = {
            resource_type: "file",
            resource_id: uuid,
            integration: model.value.selected,
            content: String(bytes),
            filepath: file.name,
            name: file.name.split('.')[0]
        }
        // for new, unsaved integrations
        if (selectedIntegration.value.resources === undefined || selectedIntegration.value.resources === null) {
            selectedIntegration.value.resources = {};
        }
        selectedIntegration.value.resources[uuid] = fileResource;
    });

    await Promise.all(promises);
}

const downloadFile = async (id) => {
    const file: IntegrationAttachedFile = selectedIntegration.value.resources[id] as IntegrationAttachedFile
    const blob = new Blob([file?.content], {type: "text/plain"})
    const url = window.URL.createObjectURL(blob);
    const temporaryElement  = document.createElement("a");
    temporaryElement.href = url;
    temporaryElement.download = file.filepath;
    temporaryElement.click();

    window.URL.revokeObjectURL(url)
    temporaryElement.remove()
};

</script>

<style lang="scss">
.integration-editor {
    display: flex;
    flex-direction: column;
    .integration-main-content {
        overflow: auto;
        display: flex;
        flex-direction: column;
        .integration-header {
            display: flex;
            flex-direction: row;
            gap: 0.5rem;
            width: 100%;
            max-width: 100%;
            flex-shrink: 0;
            > div.p-select {
                flex: 1 1 auto;
                width: 100px;
                span.p-select-label {
                    flex-shrink: 2;
                    display: block;
                    min-width: 0;
                }
            }
            > div.p-splitbutton {
                flex-shrink: 0;
            }
        }
    }
    padding: 0 0.4rem;
    height: 100%
}

.constrained-editor-height {
    max-height: 16rem;
    overflow-y: auto;
}

.integration-editor > fieldset.p-fieldset legend.p-fieldset-legend {
    display: flex;
}
</style>
