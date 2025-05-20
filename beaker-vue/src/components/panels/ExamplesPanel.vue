<template>
    <div class="datasource-panel">
        <InputGroup>
            <InputGroupAddon>
                <i class="pi pi-search"></i>
            </InputGroupAddon>
            <InputText placeholder="Search Examples..." v-model="searchText">
            </InputText>
            <Button
                v-if="searchText !== undefined && searchText !== ''"
                icon="pi pi-times"
                severity="danger"
                @click="() => {searchText = undefined}"
                v-tooltip.left="'Clear Search'"
            />
        </InputGroup>
        <Button
            style="height: 32px; width: fit-content; flex-shrink: 0;"
            icon="pi pi-plus"
            label="Add New Example"
            :disabled="disabled"
            @click="newExample"
        />
        <div
            style="
                display: flex;
                flex-direction: column;
                padding-top: 0.25rem;
                padding-bottom: 0.25rem;
                gap: 0.5rem;
                width: 100%;
            "
        >
            <i>{{ (selectedDatasource?.examples ?? []).length }} examples available:</i>
        </div>
        <div class="datasource-editor-list">
            <div
                class="datasource-card"
                v-for="(example, index) in (selectedDatasource?.examples ?? [])"
                :key="index"
                :class="exampleState[index] === 'hidden' ? 'hidden-box-shadow' : ''"
            >
                <Card v-show="searchFilter(searchText, example?.query, example?.notes)">
                    <template #title>
                        <div class="datasource-editor-card-title">
                            <div class="datasource-editor-button-container">
                                <div class="datasource-buttons-left">
                                    <Button
                                        outlined
                                        icon="pi pi-pencil"
                                        label="Edit"
                                        v-if="exampleState[index] !== 'editing'"
                                        @click="editExample(index)"
                                    />
                                    <Button
                                        outlined
                                        :icon="`pi ${exampleState[index] === 'showMore' ? 'pi-chevron-down' : 'pi-chevron-right'}`"
                                        @click="
                                            exampleState[index] = (exampleState[index] === 'showMore')
                                                ? 'hidden'
                                                : 'showMore'
                                        "
                                        :label="exampleState[index] === 'showMore' ? 'Collapse' : 'Expand'"
                                        v-if="exampleState[index] !== 'editing'"
                                    />
                                    <Button
                                        :icon="`pi pi-save`"
                                        @click="saveExample(index)"
                                        label="Save Example"
                                        v-if="exampleState[index] === 'editing'"
                                        style="width: fit-content;"
                                        severity="success"
                                    />
                                </div>
                                <div class="datasource-buttons-right">
                                    <Button
                                        severity="warning"
                                        icon="pi pi-times"
                                        @click="
                                            exampleState[index] = 'hidden';
                                            exampleChanges = undefined;
                                        "
                                        label="Cancel Editing"
                                        style="width: fit-content;"
                                        v-if="exampleState[index] === 'editing'"
                                    />
                                    <Button
                                        icon="pi pi-times"
                                        severity="danger"
                                        v-tooltip="'Delete Example'"
                                        v-if="exampleState[index] !== 'editing'"
                                        @click="deleteExample(index)"
                                    />
                                </div>
                            </div>
                            <Divider></Divider>
                            <span
                                class="datasource-editor-card-title-text"
                                v-if="exampleState[index] !== 'editing'"
                            >
                                {{ example?.query }}
                            </span>
                            <Divider v-if="exampleState[index] !== 'editing'"></Divider>
                        </div>
                    </template>
                    <template #content>
                        <div
                            class="datasource-editor-main-content"
                            :style="`
                                display: flex;
                                overflow: hidden;
                                ${exampleState[index] === 'showMore' ? '' : 'height: 6rem;'}
                                flex-direction: ${exampleState[index] === 'showMore' ? 'column' : 'row'};
                            `"
                            v-show="exampleState[index] !== 'editing'"
                        >
                            <div
                                :style="`${exampleState[index] === 'showMore' ? '' : 'width: 50%;'}`"
                            >
                                <p style="white-space: pre-wrap;">
                                    {{ (example?.notes ?? "") === ""
                                            ? "No description provided for this example."
                                            : example.notes
                                    }}
                                </p>
                            </div>
                            <div
                                :style="`${exampleState[index] === 'showMore' ? '' : 'width: 50%;'}`"
                            >
                                <CodeEditor
                                    v-model="example.code"
                                    placeholder="Example is empty."
                                    :readonly="true"
                                    language="python"
                                    ref="examplePreviewCodeEditors"
                                />
                            </div>
                        </div>
                        <div
                            v-if="exampleState[index] === 'editing'"
                            class="datasource-editor-main-content"
                            style="flex-direction: column;"
                        >
                            <Fieldset legend="Query">
                                <p>The query tells the specialist agent what task this example is for, e.g. "Fetch and display specific studies about a given topic.".</p>
                                <div class="constrained-editor-height">
                                    <CodeEditor
                                        v-if="exampleChanges?.query !== undefined"
                                        v-model="exampleChanges.query"
                                    />
                                </div>
                            </Fieldset>
                            <Fieldset legend="Description">
                                <p>Providing a description helps the specialist agent know when and in what cases this examples is useful.</p>
                                <div class="constrained-editor-height">
                                    <CodeEditor
                                        v-if="exampleChanges?.notes !== undefined"
                                        v-model="exampleChanges.notes"
                                    />
                                </div>
                            </Fieldset>
                            <Fieldset legend="Code">
                                <p>Code given for a specific example helps the specialist agent use a known-working approach to handle the user's request.</p>
                                <div class="constrained-editor-height">
                                    <CodeEditor
                                        v-if="exampleChanges?.code !== undefined"
                                        v-model="exampleChanges.code"
                                        language="python"
                                    />
                                </div>
                            </Fieldset>
                        </div>
                    </template>
                </Card>
            </div>
        </div>
    </div>
</template>


<script setup lang="ts">

import { ref, nextTick, defineEmits, defineModel, defineProps } from 'vue';
import Fieldset from 'primevue/fieldset';
import Button from "primevue/button";
import Divider from 'primevue/divider';
import Card from 'primevue/card';
import InputGroup from "primevue/inputgroup";
import InputGroupAddon from "primevue/inputgroupaddon";
import InputText from "primevue/inputtext";
import CodeEditor from '../misc/CodeEditor.vue';
import { type Example } from '../misc/DatasourceEditor.vue'

type ExampleState = "hidden" | "showMore" | "editing"

const emit = defineEmits(['onchange'])
const props = defineProps<{
    disabled?: boolean
}>()

const exampleState = ref<ExampleState[]>([]);
const selectedDatasource = defineModel<{examples?: Example[]}>()
const exampleChanges = ref<Example>(undefined);
const examplePreviewCodeEditors = ref<(typeof CodeEditor)[]>();
const searchText = ref<string>();

// note: filteredExamples as a ComputedRef would be good here, but it makes the codemirror refs harder to reason about.
// instead, we use v-show at the point of rendering the card itself to test membership in the filter
const searchFilter = (target?: string, name?: string, desc?: string) => {
    if (target === undefined) {
        return true;
    }
    const targetLower = target.toLowerCase();
    const nameLower = (name ?? "").toLowerCase()
    const descLower = (desc ?? "").toLowerCase()

    return targetLower.trim() === ""
        || nameLower.includes(targetLower)
        || descLower.includes(targetLower);
}

// codemirror sources aren't quite reactive without actions firing, so saving a new example
// or removing existing examples should point the model to the correct reference
const updateEditorRefs = () => {
    const examples = selectedDatasource.value?.examples;
    if (examples === undefined || examples.length === 0) {
        return;
    }
    if (examplePreviewCodeEditors.value !== undefined) {
        for (let index = 0; index < examples.length; index++) {
            if (exampleState.value?.[index] === 'editing') {
                continue
            } else {
                examplePreviewCodeEditors.value[index].model = examples[index]?.code
            }
        }
    }
}

const editSingleExample = (index) => {
    exampleState.value[index] = 'editing';
    for (let i = 0; i < exampleState.value.length || 0; i++) {
        if (exampleState.value[i] === 'editing' && i != index) {
            exampleState.value[i] = 'hidden';
        }
    }
}

const newExample = () => {
    let examples = selectedDatasource.value?.examples;

    if (examples === undefined) {
        examples = []
    }

    examples.unshift({
        query: 'New Example',
        notes: '',
        code:  ''
    })
    exampleState.value.unshift('editing');
    exampleChanges.value = {...examples[0]}

    editSingleExample(0);
    nextTick(() => updateEditorRefs())
}

const editExample = (index) => {
    let examples = selectedDatasource.value?.examples;

    editSingleExample(index);

    exampleChanges.value = {
        notes: '',
        ...examples?.[index]
    }
}

const saveExample = (index) => {
    let examples = selectedDatasource.value?.examples;
    exampleState.value[index] = 'hidden';

    examples[index] = exampleChanges.value;
    exampleChanges.value = undefined;

    emit('onchange')
    nextTick(() => updateEditorRefs());
}

const deleteExample = (index) => {
    let examples = selectedDatasource.value?.examples;

    examples.splice(index, 1);
    exampleState.value.splice(index, 1);

    emit('onchange')
    nextTick(() => updateEditorRefs());
}

</script>

<style lang="scss">

.datasource-panel {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding-right: 0.5rem;

    .p-fieldset {
        input {
            max-width: 100%;
            width: 100%;
        }
        textarea {
            max-width: 100%;
            width: 100%;
        }

        max-width: 100%;
        .p-fieldset-legend {
            max-width: 100%;
            background: none;
            padding: 0.5rem;
            .p-dropdown {
                margin-right: 0.5rem;
            }
        }
        margin-bottom: 1rem;

        .p-fieldset-content {
            max-width: 100%;
            padding: 0.5rem;
            display: flex;
            flex-direction: column;
            div.p-toolbar {
                max-width: 100%;
                padding: 0.5rem;
                margin-bottom: 0.5rem;
                // &:nth-child(1) {
                //     margin-bottom: 0rem;
                // }
                .p-toolbar-group-start {
                    button {
                        margin-right: 0.5rem
                    }
                }
            }
            > .p-inputtextarea.p-inputtext {
                height: 10rem;
            }
            > p {
                margin-top: 0rem;
            }
        }
    }
}

.datasource-editor-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    overflow: auto;
    // top card box shadow
    padding: 0.2rem;
    div.p-card .p-card-content {
        padding: 0.25rem 0;
    }
    div.p-card-body {
        padding: 0.75rem 0.75rem;
    }
}

.datasource-editor-card-title {
    display: flex;
    flex-direction: column;
    div.p-divider.p-divider-horizontal {
        margin: 0.5rem 0;
    }
    .datasource-editor-button-container {
        height: 2.4rem;
        padding: 0.2rem;
        width: 100%;
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        button {
            width: fit-content;
            height: 32px;
            padding: 0 0.5rem;
        }
        .datasource-buttons-left {
            button {
                margin-right: 0.5rem;
            }
        }
        .datasource-buttons-right {
            button {
                margin-left: 0.5rem;
            }
        }

    }
    .datasource-editor-card-title-text {
        flex: 1 1;
        font-size: 0.95rem;
        margin: auto;
        margin-left: 0;
        font-weight: 500;
    }
}


// for inner h1 being larger than header; rescale to make sensible whitespace
.datasource-editor-main-content {
    p, ul, li { margin-bottom: 0.8rem; margin-top: 0rem; }
    > *:nth-child(1) {
        margin-top: 0rem;
    }
    font-size: 0.8rem;
    display: flex;
}
</style>
