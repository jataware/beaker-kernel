<template>
    <div class="config-panel-container">
        <div class="config-option" :class="value.type.type_str" v-for="(value, key) in schema" v-bind:key="key">
            <label :for="key">{{ key }}</label>
            <small>{{ value.description }}</small>
            <InputText
                v-if="value.metadata?.sensitive"
                :id="key"
                :name="key"
                ref="inputRefs"
                v-model="inputModel[key]"
                :feedback="false"
                type="password"
                placeholder="Leave blank to keep unchanged."
            />
            <InputText
                v-else-if="value.type.type_str.startsWith('str')"
                :id="key"
                :name="key"
                ref="inputRefs"
                v-model="inputModel[key]" @change="console.log('change')"

            />
            <InputSwitch
                v-else-if="value.type.type_str == 'bool'"
                :id="key"
                style="padding: 2px 8px;"
                :name="key"
                ref="inputRefs"
                v-model="inputModel[key]"
            />
            <div
                v-else-if="key == 'tools_enabled'"
            >
                <DataTable
                    :value="inputModel[key]"
                    editMode="cell"
                >
                    <Column header="Name" field="name">
                        <template #editor="dataprops">
                            <InputText
                                v-model="dataprops.data.name"
                                autofocus
                                :original-value="new String(toRaw(dataprops.data.name))"
                                @change="() => {inputModel[key][dataprops.index][dataprops.field] = dataprops.data.name;}"
                            />
                        </template>
                    </Column>
                    <Column header="Enabled" field="value">
                        <template #body="{ data }">
                            <InputSwitch
                                style="padding: 2px 8px;"
                                v-model="data.value"
                            />
                        </template>
                    </Column>
                    <Column :sortable="false">
                        <template #header>
                            <i class="pi pi-trash"></i>
                        </template>
                        <template #body="{index}">
                            <Button
                                icon="pi pi-trash"
                                style="width: 1.8rem; height: 1.8rem;"
                                @click="(inputModel[key] as object[]).splice(index, 1);"
                            />
                        </template>
                    </Column>
                </DataTable>
                <Button icon="pi pi-plus" @click="add_tool"/>
            </div>
        </div>
        <div>
        <Button
            @click="save"
            label="Save"
            style="margin-right: 1rem;"
        />
        <Button
            @click="reset"
            label="Reset"
        />
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, reactive, defineEmits, toRaw, shallowReactive, triggerRef, onBeforeMount, computed, inject, onMounted, ShallowReactive, shallowRef } from "vue";
import Tree from 'primevue/tree';
import { TreeNode } from 'primevue/treenode';
import Accordion from "primevue/accordion";
import AccordionTab from "primevue/accordiontab";
import DataView from "primevue/dataview";
import { emitError } from "vue-json-pretty/types/utils";
import Listbox from "primevue/listbox";
import InputText from "primevue/inputtext";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import ToggleButton from "primevue/togglebutton";
import InputSwitch from "primevue/inputswitch";
import Button from "primevue/button";
import { BeakerSessionComponentType } from '../session/BeakerSession.vue';

const beakerSession = inject<BeakerSessionComponentType>("beakerSession");

const config = ref<object>();
const schema = ref<object>();
const inputRefs = ref([]);
const inputModel = ref<object>({});
const undoHistory = ref<string[]>();

const toolsEnabled = shallowRef<{name: string, value: boolean}[]>();

const add_tool = () => {
    inputModel.value.tools_enabled.push({
        name: '',
        value: false
    });
}

const save = async () => {
    console.log({inputModel, schema, toolsEnabled, config, undoHistory})
}

const reset = async () => {
        const serverSettings = beakerSession.session.services.serverSettings;
        const configUrl = `${serverSettings.baseUrl}config/control`;
        const schemaUrl = configUrl + '?schema';
        const configFuture = fetch(configUrl);
        const schemaFuture = fetch(schemaUrl);
        const configResponse = await configFuture
        const schemaResponse = await schemaFuture
        const schemaJson = await schemaResponse.json();
        const configJson = await configResponse.json();
        schema.value = schemaJson;
        config.value = configJson;
        inputModel.value = Object.assign({}, configJson.config);
        inputModel.value.tools_enabled = Object.entries(configJson.config.tools_enabled).map(([k, v]) => {return {name: k, value: v}});
        undoHistory.value = [JSON.stringify(inputModel.value)];
}

onBeforeMount(() => {
    beakerSession.session.sessionReady.then(async () => {
        reset();
    });
})

</script>


<style lang="scss">
.config-panel-container {
    padding: 1rem;
}

.config-option {
    display: flex;
    flex-direction: column;
    margin-bottom: 1.5rem;

    & > *{
        margin-left: 1rem;
    }

    & label {
        margin-left: 0;
        font-weight: bold;
        margin-bottom: 0.2rem;
    }
}



</style>
