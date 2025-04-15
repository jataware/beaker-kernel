<template>
    <div class="datasource-editor">
        <Fieldset>
            <template #legend>
                <Dropdown :options="
                    datasources.map((datasource) => {
                        return {
                            label: datasource.name,
                            value: datasource
                        }
                    })"
                option-label="label"
                option-value="value"
                v-model="selectedDatasource">

                </Dropdown>

                <Button>
                    Create New Datasource
                </Button>
            </template>

            <Fieldset legend="Name">
                <InputText
                    v-if="selectedDatasource?.name"
                    v-model="selectedDatasource.name"
                >
                </InputText>
                <InputText v-else disabled></InputText>
            </Fieldset>

            <Fieldset legend="Description">
                <Textarea
                    v-if="selectedDatasource?.description"
                    v-model="selectedDatasource.description"
                >
                </Textarea>
                <Textarea v-else disabled filled></Textarea>
            </Fieldset>

            <Fieldset legend="User Files" v-if="selectedDatasource?.attached_files">
                <Toolbar v-for="file in selectedDatasource.attached_files" :key="file?.filepath">
                    <template #start>
                        <Button
                            icon="pi pi-download"
                            v-tooltip="'Download'"
                            style="width: 32px; height: 32px"
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
                <Button>
                    Add New File
                </Button>
            </Fieldset>

            <Fieldset legend="Details">
                <Textarea
                    v-if="selectedDatasource?.source"
                    v-model="selectedDatasource.source"
                >
                </Textarea>
                <Textarea v-else disabled filled></Textarea>
            </Fieldset>

            <Button @click="save">Save</Button>

            <Divider></Divider>

            <Fieldset legend="Examples">

            </Fieldset>
        </Fieldset>
    </div>
</template>


<script setup lang="ts">

import { defineProps, ref, defineEmits, watch, provide, computed, nextTick, onMounted, inject, toRaw, isReactive, reactive } from 'vue';
import { BeakerSession } from 'beaker-kernel/src';

import Dropdown from 'primevue/dropdown';
import Fieldset from 'primevue/fieldset';
import Textarea from "primevue/textarea";
import Button from "primevue/button";
import Divider from 'primevue/divider';
import Toolbar from 'primevue/toolbar';
import InputText from 'primevue/inputtext';

const props = defineProps(["datasources"]);
const selectedDatasource = ref();

const session = inject<BeakerSession>('session');

const save = () => session.executeAction('save_datasource', selectedDatasource?.value)

</script>
