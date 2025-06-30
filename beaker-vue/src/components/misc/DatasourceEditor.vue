<template>
    <div class="datasource-editor">
        <div class="datasource-loading" v-if="beakerSession.status === 'connecting'">
            <ProgressSpinner></ProgressSpinner>
            Loading integrations...
            {{beakerSession?.status}}
        </div>

        <Fieldset v-else>
            <template #legend>
                <Dropdown :options="
                    allDatasources.map((datasource) => {
                        return {
                            label: datasource.name,
                            value: datasource
                        }
                    })"
                :option-label="(option) => option?.label ?? 'Select integration...'"
                option-value="value"
                placeholder="Select a integration..."
                @click="(event) => {
                    if (!confirmUnsavedChanges()) {
                        event.preventDefault;
                    } else {
                        unsavedChanges = false;
                        temporaryDatasource = undefined;
                    }
                }"
                v-model="selectedDatasource">

                </Dropdown>

                <SplitButton
                    @click="() => {
                        if (confirmUnsavedChanges()) {
                            newDatasource();
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

                <span v-if="unsavedChanges">
                    Unsaved changes!
                </span>

            </template>

            <Fieldset legend="Name">
                <InputText
                    v-if="selectedDatasource"
                    v-model="selectedDatasource.name"
                    :placeholder="selectedDatasource?.name ? 'Name' : 'No integration selected.'"
                    @change="unsavedChanges = true;"
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
                        v-if="selectedDatasource"
                        v-model="selectedDatasource.description"
                        @change="setUnsavedChanges"
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
                <Toolbar v-for="file in selectedDatasource?.attached_files" :key="file?.filepath">
                    <template #start>
                        <Badge
                            severity="warning"
                            size="large"
                            v-if="!RegExp(`\{${file?.name}\}`).test(selectedDatasource?.source)"
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
                            icon="pi pi-times"
                            severity="danger"
                            style="width: 32px; height: 32px"
                            @click="() => {
                                selectedDatasource.attached_files = selectedDatasource.attached_files.splice(
                                    selectedDatasource.attached_files.indexOf(file), 1
                                )
                            }"
                            v-tooltip="'Remove File'"
                        />
                    </template>
                </Toolbar>
                <Button @click="openFileSelectionMultiple" style="width: fit-content;">
                    Add New Files
                </Button>
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
                        v-if="selectedDatasource"
                        v-model="selectedDatasource.source"
                        @change="setUnsavedChanges"
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


            <Divider></Divider>

            <div style="display: flex; flex-direction: column; gap: 0.5rem">
                <Button
                    style="width: fit-content"
                    @click="save"
                    :disabled="!selectedDatasource"
                >Save</Button>
            </div>

        </Fieldset>
    </div>
</template>


<script setup lang="ts">

import { defineProps, ref, defineEmits, watch, provide, computed, nextTick, onMounted, inject, toRaw, isReactive, reactive } from 'vue';
import { BeakerSession } from 'beaker-kernel/src';
import { BeakerSessionComponentType } from '../session/BeakerSession.vue';

import Dropdown from 'primevue/dropdown';
import Fieldset from 'primevue/fieldset';
import Button from "primevue/button";
import Divider from 'primevue/divider';
import Toolbar from 'primevue/toolbar';
import InputText from 'primevue/inputtext';
import ProgressSpinner from 'primevue/progressspinner';
import Tag from 'primevue/tag';

import cookie from 'cookie';

import { ContentsManager, Contents } from '@jupyterlab/services';
import Badge from 'primevue/badge';
import CodeEditor from './CodeEditor.vue';
import SplitButton from 'primevue/splitbutton';
const showToast = inject<any>('show_toast');

const props = defineProps(["datasources", "selectedOnLoad", "folderRoot"]);
const selectedDatasource = ref(undefined);
const temporaryDatasource = ref(undefined);

const hasLoadedInitialSelection = ref(false);

const sortedDatasources = computed(() =>
    props?.datasources?.toSorted((a, b) => a?.name.localeCompare(b?.name)))

const allDatasources = computed(() =>
    [...sortedDatasources?.value, ...(temporaryDatasource?.value ? [temporaryDatasource.value] : [])])

watch(props.datasources, (updatedDatasources) => {
    if (updatedDatasources.length === 0) {
        return;
    }
    if (hasLoadedInitialSelection.value) {
        return;
    }
    if (props?.selectedOnLoad) {
        nextTick(() => {
            if (props?.selectedOnLoad === 'new') {
                newDatasource();
                return;
            }
            for (const datasource of updatedDatasources) {
                if (datasource?.slug === props?.selectedOnLoad) {
                    selectedDatasource.value = datasource;
                    return;
                }
            }
        })
    }
    hasLoadedInitialSelection.value = true;
})

const descriptionEditor = ref();
watch(() => [selectedDatasource.value?.description], (current) => {
    if (descriptionEditor.value) {
        descriptionEditor.value.model = current[0];
    }
})

const instructionEditor = ref();
watch(() => [selectedDatasource.value?.source], (current) => {
    if (instructionEditor.value) {
        instructionEditor.value.model = current[0];
    }
})

const session = inject<BeakerSession>('session');
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");

const emptyText = ref<string|undefined>(undefined);

const fileInput = ref<HTMLInputElement|undefined>(undefined);
const fileInputMultiple = ref<HTMLInputElement|undefined>(undefined);
const uploadForm = ref<HTMLFormElement|undefined>(undefined);
const uploadFormMultiple = ref<HTMLFormElement|undefined>(undefined);

const unincludedFiles = computed(() =>
    (selectedDatasource?.value?.attached_files ?? [])
        ?.map((file) =>
            RegExp(`{${file?.name}}`).test(selectedDatasource?.value?.source) ? false : file?.name)
        ?.filter((x) => x))

const unsavedChanges = ref(false);
const setUnsavedChanges = () => {unsavedChanges.value = true;};
const confirmUnsavedChanges = () => {
    if (unsavedChanges?.value) {
        return confirm("You currently have unsaved changes that would be lost with this change. Are you sure?")
    }
    return true;
}

watch(unsavedChanges, async (newValue, _) => {
    if (newValue) {
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

const slugWrapper = computed(() => {
    if (selectedDatasource?.value?.slug) {
        return selectedDatasource.value.slug;
    }
    return selectedDatasource?.value?.name?.toLowerCase().replaceAll(' ', '_');
})

const contentManager = new ContentsManager({});
const cookies = cookie.parse(document.cookie);
const xsrfCookie = cookies._xsrf;

const folderSlug = computed(() => {
    let url = selectedDatasource?.value?.url;
    if (url === undefined || url === null || url === '') {
        return slugWrapper.value;
    }
    else if (url.endsWith('api.yaml')) {
        return url.slice(0, -1 * ("/api.yaml".length))
    }
    return url
})

const newDatasource = () => {
    unsavedChanges.value = true;
    selectedDatasource.value = {
        name: "New Integration",
        url: "",
        slug: undefined,
        source: "This is the prompt information that the agent will consult when using the integration. Include API details or how to find datasets here.",
        description: "This is the description that the agent will use to determine when this integration should be used.",
        attached_files: [],
    }
    temporaryDatasource.value = selectedDatasource.value
}

const save = async () => {
    unsavedChanges.value = false;
    temporaryDatasource.value = undefined;

    try {
        await createFoldersForDatasource();
        await writeDatasource(selectedDatasource.value);

        const action = session.executeAction('save_datasource', {
            ...selectedDatasource.value,
            slug: slugWrapper.value
        });
        const response = await action.done;
        if (response.content?.status === "ok") {
            showToast({
                title: 'Saved!',
                detail: `The session will now reconnect and load the new definition.`,
                severity: 'success',
                life: 4000
            });
        }
    }
    catch (error) {
        showToast({
            title: 'Failed to save integration',
            detail: `${error}`,
            severity: 'danger',
            life: 4000
        });
    }
}

const download = async (name) => {
    const folderRoot = props.folderRoot;
    const path = `${folderRoot}/${folderSlug.value}/documentation/${name}`;
    await downloadFile(path);
}

const createFoldersForDatasource = async () => {
    const folderRoot = props.folderRoot;
    const basepath = `${folderRoot}/${folderSlug.value}`

    // is the datasource slug folder present?
    try {
        const targetDir = await contentManager.get(basepath);
        if (targetDir.type !== 'directory') {
            throw "Slug overlaps with existing non-directory file."
        }
    }
    catch (e) {
        const directory = await contentManager.newUntitled({
            path: folderRoot,
            type: 'directory'
        })
        await contentManager.rename(directory.path, basepath);
    }

    // what about documentation/?
    try {
        const targetDir = await contentManager.get(`${basepath}/documentation`);
        if (targetDir.type !== 'directory') {
            throw "slug/documentation overlaps with existing non-directory file. Is there a file named 'documentation' with no extension?"
        }
    }
    catch (e) {
        const subdirectory = await contentManager.newUntitled({
            path: basepath,
            type: 'directory'
        })
        await contentManager.rename(subdirectory.path, `${basepath}/documentation`)
    }
}

const onSelectFileForUpload = async () => {
    const fileList = uploadForm.value['uploadfiles']?.files;
    await createFoldersForDatasource();
    await uploadFile(fileList);
}


const onSelectFilesForUpload = async () => {
    const fileList = uploadFormMultiple.value['uploadfilesMultiple']?.files;
    await createFoldersForDatasource();
    await uploadFile(fileList);
    for (const file of fileList) {
        selectedDatasource?.value.attached_files.push({
            name: file.name.split('.').slice(0, -1).join(''),
            filepath: file.name
        })
    }

}

const formatDatasource = (datasource: {
    name: string,
    description: string,
    source: string,
    attached_files: any[]
}): string => {
    const slug = slugWrapper.value;
    const indentLines = (text: string) => text
        .split('\n')
        .map(line => `\n    ${line}`)
        .join('')
        .trim()
    const indentedDescription = indentLines(datasource?.description ?? "")
    const indentedContents = indentLines(datasource?.source ?? "")
    const filePayload = (datasource?.attached_files ?? [])
        .map(attachment =>
            `${attachment.name}: !load_txt documentation/${attachment.filepath}\n`)
        .join('\n')

    const template = `
name: ${datasource.name}
slug: ${slug}
cache_key: api_assistant_${slug}
examples: !load_yaml documentation/examples.yaml

description: |
    ${indentedDescription}

${filePayload}

documentation: !fill |
    ${indentedContents}
`
    return template;
}

const writeDatasource = async (datasource) => {
    const formattedDatasource = formatDatasource(datasource)
    const folderRoot = props.folderRoot;
    const basepath = `${folderRoot}/${folderSlug.value}`

    const type = 'text/plain'
    const format = 'text';
    const fileObj: Partial<Contents.IModel> = {
        type,
        format,
        content: formattedDatasource,
    };
    let result;
    try {
        result = await contentManager.save(`${basepath}/api.yaml`, fileObj);
        result = await contentManager.save(`${basepath}/documentation/examples.yaml`, {type, format, content: btoa("")});
    }
    catch(e) {
        showToast({
            title: 'Upload failed',
            detail: `Unable to upload file "${basepath}/api.yaml": ${e}`,
            severity: 'error',
            life: 8000
        });
        return;
    }

}

const uploadFile = async (files: FileList) => {
    const folderRoot = props.folderRoot;
    unsavedChanges.value = true;
    const promises = Array.from(files).map(async (file) => {
        let path = `${folderRoot}/${folderSlug.value}/documentation/${file.name}`;
        if (fileTarget?.value !== undefined) {
            path = `${folderRoot}/${folderSlug.value}/documentation/${fileTarget.value}`;
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
.constrained-editor-height {
    max-height: 16rem;
    overflow-y: auto;
}

.datasource-editor > fieldset.p-fieldset legend.p-fieldset-legend {
    display: flex;
}
</style>
