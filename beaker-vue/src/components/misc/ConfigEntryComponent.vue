<template>
    <template v-if="schema?.type_str?.startsWith('Dataclass')">
        <div
            class="config-option dataclass"
            :type-str="dataclassItemSchema?.type_str"
            v-for="(dataclassItemSchema, dataclassItemKey) in (schema.fields)"
            :key="`${keyValue}-${dataclassItemKey}`"
        >
            <label :for="(dataclassItemKey as unknown as string)">{{ dataclassItemKey }}</label>
            <small>{{ dataclassItemSchema.description }}</small>
            <ConfigEntryComponent
                :schema="dataclassItemSchema"
                :name="(dataclassItemKey as unknown as string)"
                :key-value="keyValue?.split('.').concat((dataclassItemKey as unknown as string)).join('.')"
                :config-object="configObject"
                v-model="model[dataclassItemKey]"
            />
        </div>
    </template>
    <template v-else-if="schema?.metadata?.sensitive && schema?.type_str?.startsWith('str') && (typeof(model) === 'string' || model === null as string)">
        <div style="display: flex; flex-direction: row;">
            <InputText
                :disabled="clearSensitive"
                style="flex: 1"
                :id="keyValue"
                :name="keyValue"
                :class="{dirty}"
                v-model="model"
                :feedback="false"
                type="password"
                :placeholder="sensitiveInputPlaceholder"
            />
            <ToggleButton
                class="clear-sensitive-checkbox"
                v-model="clearSensitive"
                on-label=""
                off-label=""
                aria-label="Clear saved value"
                v-tooltip="'Clear saved value'"
                @change="handleSensitiveClearChange"
            >
                <template #icon="{value}">
                    <span class="clear-icon pi pi-eraser" :class="{checked: value}"></span>
                </template>
            </ToggleButton>
        </div>
    </template>
    <template v-else-if="schema?.type_str?.startsWith('Choice') || (schema?.type_str?.startsWith('str') && schema?.metadata?.options)">
        <!-- TODO: Replace this with a primevue dropdown when bug is fixed -->
        <div class="select-wrap p-dropdown" :class="{dirty}">
            <div class="select-dropdown p-dropdown-trigger">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg" class="p-icon p-dropdown-trigger-icon" aria-hidden="true" data-pc-section="dropdownicon"><path d="M7.01744 10.398C6.91269 10.3985 6.8089 10.378 6.71215 10.3379C6.61541 10.2977 6.52766 10.2386 6.45405 10.1641L1.13907 4.84913C1.03306 4.69404 0.985221 4.5065 1.00399 4.31958C1.02276 4.13266 1.10693 3.95838 1.24166 3.82747C1.37639 3.69655 1.55301 3.61742 1.74039 3.60402C1.92777 3.59062 2.11386 3.64382 2.26584 3.75424L7.01744 8.47394L11.769 3.75424C11.9189 3.65709 12.097 3.61306 12.2748 3.62921C12.4527 3.64535 12.6199 3.72073 12.7498 3.84328C12.8797 3.96582 12.9647 4.12842 12.9912 4.30502C13.0177 4.48162 12.9841 4.662 12.8958 4.81724L7.58083 10.1322C7.50996 10.2125 7.42344 10.2775 7.32656 10.3232C7.22968 10.3689 7.12449 10.3944 7.01744 10.398Z" fill="currentColor"></path></svg>
            </div>
            <select v-model="model" class="p-inputtext" v-if="schema?.type_str?.startsWith('Choice')" >
                <option value="" disabled>Select an option</option>
                <option v-for="(_opt, opt_name) in configObject[schema?.choice_source] || {}" :value="opt_name" :key="opt_name">
                    {{ opt_name }}
                </option>
            </select>
            <select v-else v-model="model" class="p-inputtext" >
                <option value="" disabled>Select an option</option>
                <option v-for="(value, name) in schema.metadata.options" :value="value" :key="name">
                    {{ name }}
                </option>

            </select>
        </div>
    </template>
    <template
        v-else-if="schema?.type_str?.startsWith('str') && (typeof(model) === 'string' || model === null as string)"
    >
        <InputText
            :id="keyValue"
            :class="{dirty}"
            :name="keyValue"
            v-model="model"
            :placeholder="schema.metadata?.placeholder_text || undefined"
        />
    </template>
    <template v-else-if="schema?.type_str == 'bool' && typeof(model) === 'boolean'">
        <div class="horizontal-flex">
        <span class="label" v-if="label">
            {{ label }}
        </span>
        <InputSwitch
            :id="keyValue"
            style="padding: 2px 8px;"
            :class="{dirty}"
            :name="keyValue"
            v-model="model"
        />
        </div>
    </template>
    <template v-else-if="schema?.type_str == 'int' && typeof(model) === 'number'">
        <div class="horizontal-flex">
        <span class="label" v-if="label">
            {{ label }}
        </span>
        <InputNumber
            :id="keyValue"
            style="padding: 2px 8px;"
            :class="{dirty}"
            :name="keyValue"
            v-model="model"
            :min="schema?.metadata?.extra?.min"
            :max="schema?.metadata?.extra?.max"
        />
        </div>
    </template>
    <template v-else-if="schema?.type_str?.startsWith('Table') && Array.isArray(model)">
        <Panel v-for="(record, index) in model" :key="`${keyValue}-${record.name}`" toggleable
            :class="{dirty: !originalValue.map(obj => obj.name).includes(record.name)}"
        >
            <template #togglericon="{collapsed}">
                <span v-if="collapsed" class="pi pi-chevron-up"></span>
                <span v-else class="pi pi-chevron-down"></span>
            </template>
            <template #header>
                <InlineInput v-model="model[index]['name']"/>
            </template>
            <template #icons>
                <Button icon="pi pi-trash" text size="small" @click="model.splice(index, 1)" v-tooltip="`Delete '${record.name}'`"/>
            </template>
            <ConfigEntryComponent
                :schema="schema.type_args[0]"
                :name="`${keyValue}.value-${index}`"
                :key-value="`${keyValue}.value-${index}`"
                :config-object="configObject"
                v-model="model[index]['value']"
                :label="schema.metadata?.label"
            />

        </Panel>
        <Button icon="pi pi-plus" @click="model.push({name: '', value: schema.type_args[0].default_value})"/>
    </template>
</template>

<script setup lang="tsx">
import { ref, watch, inject, onBeforeMount, onMounted, toRaw, getCurrentInstance, computed} from "vue";
import InlineInput from "./InlineInput.vue";
import InputNumber from "primevue/inputnumber";
import InputText from "primevue/inputtext";
import Panel from "primevue/panel";
import InputSwitch from "primevue/inputswitch";
import Button from "primevue/button";
import scrollIntoView from "scroll-into-view-if-needed";
import ToggleButton from "primevue/togglebutton";
import { IConfigDefinitions, ISchema } from "../panels/ConfigPanel.vue";

export interface ConfigEntryComponentProps {
    name?: string;
    schema: ISchema;
    configObject: IConfigDefinitions;
    keyValue: string;
    label?: string;
    sensitive?: boolean;
}

const props = withDefaults(defineProps<ConfigEntryComponentProps>(),
    {
        sensitive: false,
    }
);
// [
//     "name",
//     "schema",
//     "configObject",
//     "keyValue",
//     "label",
//     "sensitive",
// ]);

const instance = getCurrentInstance();
const model = defineModel();
const showToast = inject<any>('show_toast');
const clearSensitive = ref(false);
const unclearedValue = ref<string>("")
const originalValue = ref<any>();

const dirty = computed<boolean>(() => {
    return clearSensitive.value || JSON.stringify(model.value) !== JSON.stringify(originalValue.value);
})

watch(model, (newValue) => {
    if (props.schema?.metadata?.sensitive && props.schema?.type_str?.startsWith('str') && !clearSensitive.value) {
        if (originalValue.value === null && newValue === "") {
            model.value = originalValue.value;
        }
    }
});

const sensitiveInputPlaceholder = computed<string>(() => {
    if (clearSensitive.value) {
        return "Value will be cleared."
    }
    else if (model.value === null) {
        return 'Leave blank to keep unchanged.';
    }
    else {
        return 'No value saved. Enter to set value.';
    }
})

const handleSensitiveClearChange = () => {
    if (clearSensitive.value) {
        unclearedValue.value = model.value as string;
        model.value = "";
    }
    else {
        model.value = unclearedValue.value;
        unclearedValue.value = null;
    }
}

onBeforeMount(() => {
    originalValue.value = structuredClone(toRaw(model.value));
});

onMounted(() => {
    if (props.schema?.type_str?.startsWith('Choice')) {
        const sourceObject = props.configObject[props.schema?.choice_source];
        if (sourceObject) {
            watch(sourceObject, () => {
                if (!sourceObject.map((obj) => obj.name).includes(model.value)) {
                    model.value = "";
                    showToast({
                        title: 'Warning',
                        detail: `Changing this value has caused property '${props.keyValue}' to become unset. \
Please make sure to update that value before saving.`,
                        severity: "warn",
                        life: 15000,
                    })
                    setTimeout(() => {
                        const div: HTMLDivElement = instance.vnode.el.parentElement;
                        scrollIntoView(
                            div,
                            {
                                scrollMode: 'if-needed',
                                block: "center",
                                behavior: 'smooth',
                            },
                        )
                        div.style.outline = "red 1px solid";
                        div.style.outlineOffset = "0.5rem";

                        setTimeout(() => {
                            div.style.outline = "unset";
                            div.style.outlineOffset = "unset";
                        }, 3000);


                    }, 500);
                }
            });
        }
    }
})


</script>

<style lang="scss">

.config-option {
    display: flex;
    flex-direction: column;
    margin-bottom: 1.5rem;

    & > * {
        margin-left: 1rem;
    }

    & label {
        margin-left: 0;
        font-weight: bold;
        margin-bottom: 0.5rem;

    }

    & .p-panel-header {
        padding-left:0.5rem;
        padding-bottom: 0.5rem;
        border-bottom: unset;
    }

    & .p-panel-content {
        padding-top: 0.5rem;
    }

    & .p-panel {
        margin-bottom: 0.5rem;
    }

    & .select-wrap {
        position: relative;
        background-color: var(--surface-b);

        & select {
            width: 100%;
            color: var(--text-color);
            background-color: transparent;
            padding-right: 2.5rem;
            z-index: 1;
            cursor: pointer;
        }

        & .select-dropdown {
            position: absolute;
            top: 0.8rem;
            right: -1rem;
            z-index: 0;
        }

        & option {
            background-color: var(--surface-a);

            &:disabled {
                color: #777;
            }
        }
    }

    .p-inplace {
        display: flex;
        flex: 1;
        padding: unset;

        &:hover {
            background: unset;
        }
    }

    .p-inplace-display {
        flex: 1;
        padding: unset;

        &:hover {
            background: unset;
        }
    }

    .p-inplace-content {
        flex: 1;
    }

    .horizontal-flex {
        display: flex;
        flex-direction: row;
        align-items: center;
        column-gap: 1rem;

        & .label {
            font-weight: bold;
        }
    }

    .p-panel-toggler {
        top: -1rem;
        right: -1rem;
    }

    .clear-icon {
        color: var(--primary-color);

        &.checked {
            color: var(--primary-color-text)
        }
    }

    .dirty {
        box-shadow: 0px 0px 5px 2px #C65BC1;
    }
}

</style>
