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
                        value: integration
                    }))"
                    :option-label="(option) => option?.label ?? 'Select integration...'"
                    option-value="value"
                    placeholder="Select a integration..."
                    @click="(event) => {
                        if (!confirmUnsavedChanges()) {
                            event.preventDefault;
                        } else {
                            // treat a new selection as
                            emit('onSave');
                            temporaryIntegration = undefined;
                        }
                    }"
                    v-model="selectedIntegration">
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
                    @change="emit('onUnsavedChange')"
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
                        @change="emit('onUnsavedChange')"
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
                <Toolbar v-for="file in selectedIntegration?.attached_files" :key="file?.filepath">
                    <template #start>
                        <Badge
                            severity="warning"
                            size="large"
                            v-if="!RegExp(`\{${file?.name}\}`).test(selectedIntegration?.source)"
                            style="margin-right: 0.5rem;"
                            v-tooltip="{
                                value: `${file?.name} is not used in the below agent instructions.
                                    If you mean for this file to be included, please ensure it is referenced
                                    with {${file?.name}} in the below agent instructions body.`,
                                pt: {
                                    root: {
                                        style: {
                                            maxWidth: undefined
                                        }
                                    }
                                }
                            }"
                        >
                            <span class="pi pi-exclamation-triangle"></span>
                        </Badge>
                        <Button
                            icon="pi pi-download"
                            v-tooltip="'Download'"
                            style="width: 32px; height: 32px"
                            @click="download(file?.filepath)"
                        />
                        <Button
                            icon="pi pi-upload"
                            v-tooltip="'Upload and replace'"
                            style="width: 32px; height: 32px"
                            @click="openFileSelection(file?.filepath)"
                        />
                    </template>
                    <template #center>
                        <InputText v-model="file.name" type="text">

                        </InputText>
                        <Button icon="pi pi-file" outlined v-tooltip="file?.filepath">

                        </Button>
                    </template>
                    <template #end>
                        <Button
                            icon="pi pi-trash"
                            severity="danger"
                            style="width: 32px; height: 32px"
                            @click="() => {
                                selectedIntegration.attached_files.splice(
                                    selectedIntegration.attached_files.indexOf(file), 1
                                )
                            }"
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
                        @change="emit('onUnsavedChange')"
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

            <Divider v-if="unincludedFiles.length > 0"></Divider>

            <div style="display: flex; flex-direction: column; gap: 0.5rem">
                <Tag
                    icon="pi pi-exclamation-triangle"
                    severity="warning"
                    size="large"
                    v-if="unincludedFiles.length > 0"
                >
                    Some files are not included: {{ unincludedFiles.join(', ') }}; see the above documentation about how to reference these files.
                </Tag>
            </div>
        </div>
        <div style="flex: 1 0; margin: 0.2rem; display: flex; justify-content: flex-end;">
            <div v-if="unsavedChanges" style="flex-shrink: 0;">
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
import { type IntegrationProviders, type Integration } from '../../util/integration';
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
import Badge from 'primevue/badge';
import CodeEditor from './CodeEditor.vue';
import SplitButton from 'primevue/splitbutton';
const showToast = inject<any>('show_toast');

const props = defineProps<{
    selectedOnLoad: string,
    unsavedChanges: boolean
}>();

const session = inject<BeakerSession>('session');
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");

const selectedIntegration = defineModel<Integration>({required: true});

// buffer for changes not yet committed
const temporaryIntegration = ref<Integration>(undefined);

const hasLoadedInitialSelection = ref(false);

const emit = defineEmits(['onUnsavedChange', 'onSave'])

const integrationProviders = computed<IntegrationProviders>(() =>
    beakerSession?.activeContext?.info?.integration_providers ?? {})

const sortIntegrations = (integrations: Integration[]): Integration[] =>
    integrations.toSorted((a, b) => a?.name.localeCompare(b?.name))

const mutableIntegrations = (providers: IntegrationProviders | undefined): Integration[] =>
    Object.keys(providers ?? {})
        .filter((name) => providers[name].mutable)
        .flatMap((name) => providers[name].integrations)

const allIntegrations = computed<Integration[]>(() =>
    [
        ...mutableIntegrations(integrationProviders?.value),
        ...(temporaryIntegration?.value
            ? [temporaryIntegration.value]
            : []
        )
    ]
)

const sortedIntegrations = computed<Integration[]>(() =>
    sortIntegrations(allIntegrations.value))

watch(integrationProviders, updatedProviders => {
    if (Object.keys(updatedProviders).length === 0) {
        return;
    }
    if (hasLoadedInitialSelection.value) {
        return;
    }
    if (props?.selectedOnLoad) {
        nextTick(() => {
            if (props?.selectedOnLoad === 'new') {
                newIntegration();
                return;
            }
            for (const integration of mutableIntegrations(updatedProviders)) {
                if (integration?.slug === props?.selectedOnLoad) {
                    selectedIntegration.value = integration;
                    return;
                }
            }
        })
    }
    hasLoadedInitialSelection.value = true;
})

const descriptionEditor = ref();
watch(() => [selectedIntegration.value?.description], (current) => {
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

const unincludedFiles = computed(() =>
    (selectedIntegration?.value?.attached_files ?? [])
        ?.map((file) =>
            RegExp(`{${file?.name}}`).test(selectedIntegration?.value?.source) ? false : file?.name)
        ?.filter((x) => x))

const confirmUnsavedChanges = () => {
    if (props.unsavedChanges) {
        return confirm("You currently have unsaved changes that would be lost with this change. Are you sure?")
    }
    return true;
}

watch(props, async ({unsavedChanges}, _) => {
    if (unsavedChanges) {
        onbeforeunload = () => true;
    } else {
        onbeforeunload = undefined;
    }
})

const fileTarget = ref();

const openFileSelection = (target) => {
    fileTarget.value = target;
    fileInput.value?.click();
}

const openFileSelectionMultiple = () => {
    fileTarget.value = undefined;
    fileInputMultiple.value?.click();
}

const contentManager = new ContentsManager({});
const cookies = cookie.parse(document.cookie);
const xsrfCookie = cookies._xsrf;

const newIntegration = () => {
    emit("onUnsavedChange")
    selectedIntegration.value = {
        name: "New Integration",
        url: "",
        slug: undefined,
        source: "This is the prompt information that the agent will consult when using the integration. Include API details or how to find datasets here.",
        description: "This is the description that the agent will use to determine when this integration should be used.",
        attached_files: [],
        examples: []
    }
    temporaryIntegration.value = selectedIntegration.value
}

const save = async () => {
    emit("onSave");
    temporaryIntegration.value = undefined;

    if (selectedIntegration.value === undefined) {
        return;
    }

    showToast({
        title: 'Saved!',
        detail: `The session will now reconnect and load the new definition.`,
        severity: 'success',
        life: 4000
    });

    // session.executeAction('save_integration', {
    //     ...selectedIntegration.value,
    // });
}

const getIntegrationRoot = async (integration) => {
    const future = session.executeAction('get_integration_root', {
        integration
    })
    return (await future.done).content?.return;
}

const download = async (name) => {
    const folderRoot = await getIntegrationRoot(selectedIntegration.value);
    const path = `${folderRoot}/documentation/${name}`;
    await downloadFile(path);
}

const onSelectFileForUpload = async () => {
    const fileList = uploadForm.value['uploadfiles']?.files;
    await uploadFile(fileList);
}

const onSelectFilesForUpload = async () => {
    const fileList = uploadFormMultiple.value['uploadfilesMultiple']?.files;
    await uploadFile(fileList);
    for (const file of fileList) {
        selectedIntegration?.value.attached_files.push({
            name: file.name.split('.').slice(0, -1).join(''),
            filepath: file.name
        })
    }

}

const uploadFile = async (files: FileList) => {
    // await session.executeAction('create_integration_folders_for_upload', {
    //     integration: selectedIntegration.value
    // }).done;

    const folderRoot = await getIntegrationRoot(selectedIntegration.value);
    emit('onUnsavedChange')
    const promises = Array.from(files).map(async (file) => {
        let path = `${folderRoot}/documentation/${file.name}`;
        if (fileTarget?.value !== undefined) {
            path = `${folderRoot}/documentation/${fileTarget.value}`;
        }

        const bytes = [];
        const reader = file.stream().getReader();
        var chunk = (await reader.read()).value;
        while (chunk?.length > 0) {
            bytes.push(Array.from(chunk, (byte) => String.fromCharCode(byte)).join(""));
            chunk = (await reader.read()).value;
        }
        const type = (file.type !== "" ? file.type : "application/octet-stream");
        const content = btoa(bytes.join(""));
        const format = 'base64';

        const fileObj: Partial<Contents.IModel> = {
            type,
            format,
            content,
        };

        let result;
        try {
            result = await contentManager.save(path, fileObj);
        }
        catch(e) {
            showToast({
                title: 'Upload failed',
                detail: `Unable to upload file "${path}": ${e}`,
                severity: 'error',
                life: 8000
            });
            return;
        }

        if (result && result.created && result.size) {
            showToast({
                title: 'Upload complete',
                detail: `File "${result.path}" (${result.size} bytes) successfully uploaded.`,
                severity: 'success',
                life: 4000
            });
        }
        else {
            showToast({
                title: 'Upload failed',
                detail: `Unable to upload file "${path}".`,
                severity: 'error',
                life: 8000
            });
        }
    });

    await Promise.all(promises);
}

const downloadFile = async (path) => {
    let url = await contentManager.getDownloadUrl(path);
    // Ensure we are downloading. Add the download query param
    if (!/download=/.test(url)) {
        if (/\?/.test(url)) {
            url = url + "&download=1"
        }
        else {
            url = url + "?download=1"
        }
    }
    window.location.href = url;
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
