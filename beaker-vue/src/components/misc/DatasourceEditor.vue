<template>
    <div class="datasource-editor">
        <div class="datasource-loading" v-if="beakerSession.status === 'connecting'">
            <ProgressSpinner></ProgressSpinner>
            Loading datasources...
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
                option-label="label"
                option-value="value"
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

                <Button @click="() => {
                    if (confirmUnsavedChanges()) {
                        newDatasource();
                    }
                }">
                    Create New Datasource
                </Button>

                <span v-if="unsavedChanges">
                    Unsaved changes!
                </span>
            </template>

            <Fieldset legend="Name">
                <InputText
                    v-if="selectedDatasource"
                    v-model="selectedDatasource.name"
                    @change="unsavedChanges = true;"
                >
                </InputText>
                <InputText v-else disabled></InputText>
            </Fieldset>

            <Fieldset legend="Description">
                <Textarea
                    v-if="selectedDatasource"
                    v-model="selectedDatasource.description"
                    @change="setUnsavedChanges"
                >
                </Textarea>
                <Textarea v-else disabled filled></Textarea>
            </Fieldset>

            <Fieldset legend="User Files" v-if="selectedDatasource?.attached_files">
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
                <Toolbar v-for="file in selectedDatasource.attached_files" :key="file?.filepath">
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
                            icon="pi pi-pencil"
                            v-tooltip="'Edit'"
                            style="width: 32px; height: 32px"
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
                        <Button>
                            Insert
                        </Button>
                    </template>
                </Toolbar>
                <Button @click="openFileSelectionMultiple">
                    Add New Files
                </Button>
            </Fieldset>

            <Fieldset legend="Agent Instructions">
                <span style="margin-bottom: 0.5rem">
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
                <Textarea
                    v-if="selectedDatasource"
                    v-model="selectedDatasource.source"
                    @change="setUnsavedChanges"
                >
                </Textarea>
                <Textarea v-else disabled filled></Textarea>
            </Fieldset>

            <Divider v-if="unincludedFiles.length > 0"></Divider>

            <Tag
                icon="pi pi-exclamation-triangle"
                severity="warning"
                size="large"
                v-if="unincludedFiles.length > 0"
            >
                Some files are not included: {{ unincludedFiles.join(', ') }}; see the above documentation about how to reference these files.
            </Tag>

            <Divider></Divider>

            <Button @click="save">Save</Button>

            <!-- <Fieldset legend="Examples"></Fieldset>  -->
        </Fieldset>
    </div>
</template>


<script setup lang="ts">

import { defineProps, ref, defineEmits, watch, provide, computed, nextTick, onMounted, inject, toRaw, isReactive, reactive } from 'vue';
import { BeakerSession } from 'beaker-kernel/src';
import { BeakerSessionComponentType } from '../session/BeakerSession.vue';

import Dropdown from 'primevue/dropdown';
import Fieldset from 'primevue/fieldset';
import Textarea from "primevue/textarea";
import Button from "primevue/button";
import Divider from 'primevue/divider';
import Toolbar from 'primevue/toolbar';
import InputText from 'primevue/inputtext';
import ProgressSpinner from 'primevue/progressspinner';
import Tag from 'primevue/tag';

import cookie from 'cookie';

import { ContentsManager, Contents } from '@jupyterlab/services';
import Chip from 'primevue/chip';
import Badge from 'primevue/badge';
const showToast = inject<any>('show_toast');

const props = defineProps(["datasources"]);
const selectedDatasource = ref(undefined);
const temporaryDatasource = ref(undefined);
const allDatasources = computed(() =>
    [...props?.datasources, ...(temporaryDatasource?.value ? [temporaryDatasource.value] : [])]
)

const session = inject<BeakerSession>('session');
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");

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
    console.log("target:", target);
    fileInput.value?.click();
}

const openFileSelectionMultiple = () => {
    fileTarget.value = undefined;
    fileInputMultiple.value?.click();
}

const slugWrapper = computed(() => {
    if (selectedDatasource?.value?.uid_or_slug) {
        return selectedDatasource.value.uid_or_slug;
    }
    return selectedDatasource?.value?.name?.toLowerCase().replaceAll(' ', '_');
})

const contentManager = new ContentsManager({});
const cookies = cookie.parse(document.cookie);
const xsrfCookie = cookies._xsrf;
// TODO: find actual folder root
const folderRoot = computed(() => "/src/biome/datasources")
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
        name: "New Datasource",
        url: "",
        uid_or_slug: undefined,
        source: "This is the prompt information that the agent will consult when using the datasource. Include API details or how to find datasets here.",
        description: "This is the description that the agent will use to determine when this datasource should be used.",
        attached_files: [],
    }
    temporaryDatasource.value = selectedDatasource.value
}

const save = () => {
    unsavedChanges.value = false;
    temporaryDatasource.value = undefined;
    console.log(selectedDatasource.value.uid_or_slug, slugWrapper.value)

    showToast({
        title: 'Saved!',
        detail: `The session will now reconnect and load the new definition.`,
        severity: 'success',
        life: 4000
    });
    session.executeAction('save_datasource', {
        ...selectedDatasource.value,
        uid_or_slug: slugWrapper.value
    });
}

const download = async (name) => {
    const path = `${folderRoot.value}/${folderSlug.value}/documentation/${name}`;
    console.log(`downloading ${name} (${path})`);
    await downloadFile(path);
}

const createFoldersForDatasource = async () => {
    const basepath = `${folderRoot.value}/${folderSlug.value}`

    // is the datasource slug folder present?
    try {
        const targetDir = await contentManager.get(basepath);
        if (targetDir.type !== 'directory') {
            throw "Slug overlaps with existing non-directory file."
        }
    }
    catch (e) {
        const directory = await contentManager.newUntitled({
            path: `${folderRoot.value}`,
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
        console.log(fileList)
        selectedDatasource?.value.attached_files.push({
            name: file.name.split('.').slice(0, -1).join(''),
            filepath: file.name
        })
    }

}

const uploadFile = async (files: FileList) => {
    unsavedChanges.value = true;
    const promises = Array.from(files).map(async (file) => {
        let path = `${folderRoot.value}/${folderSlug.value}/documentation/${file.name}`;
        if (fileTarget?.value !== undefined) {
            path = `${folderRoot.value}/${folderSlug.value}/documentation/${fileTarget.value}`;
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
