<template>
    <div class="examples-panel">
        <div
            class="header-controls"
            v-if="panelState.view === 'tableOfContents'"
        >
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
                <i>{{ (selectedIntegration?.examples ?? []).length }} examples available:</i>
            </div>
        </div>

        <div
            class="examples-editor-list"
            v-if="panelState.view === 'tableOfContents'"
        >
            <div
                class="example-card"
                v-for="(example, index) in (selectedIntegration?.examples ?? [])"
                :key="index"
                @mouseleave="hoveredExample = undefined"
                @mouseenter="hoveredExample = index"
            >
                <Card
                    v-if="searchFilter(searchText, example?.query, example?.notes)"
                    @click="editExample(index)"
                    :pt = "{
                        root: {
                            style:
                                'transition: background-color 150ms linear;' +
                                (hoveredExample === index
                                    ? 'background-color: var(--surface-100); cursor: pointer;'
                                    : '')
                        }
                    }"
                >
                    <template #title>
                        <div class="example-editor-card-title">
                            <span
                                class="example-editor-card-title-text"
                            >
                                {{ example?.query }}
                            </span>
                            <i
                                class="pi pi-chevron-right example-arrow"
                                :style="hoveredExample === index ? 'opacity: 1;' : 'opacity: 0;'"
                            >
                            </i>
                        </div>
                    </template>
                </Card>
            </div>
        </div>
        <div
            class="example-editor-focused"
            v-else-if="panelState.view === 'focused'"
        >
            <div class="example-editor-button-container">
                <div class="example-buttons-left">
                    <Button
                        severity="warning"
                        icon="pi pi-arrow-left"
                        @click="
                            panelState = {view: 'tableOfContents'}
                            exampleChanges = undefined;
                        "
                        label="Cancel Editing"
                        style="width: fit-content;"
                    />
                </div>
                <div class="example-buttons-right">
                    <Button
                        icon="pi pi-trash"
                        severity="danger"
                        label="Delete Example"
                        @click="deleteExample(panelState.focusedExample)"
                    />
                </div>
            </div>
            <div
                class="example-editor-main-content"
                style="flex-direction: column;"
            >
                <Fieldset legend="Query">
                    <p>The query tells the specialist agent what task this example is for, e.g. "Fetch and display specific studies about a given topic.".</p>
                    <div>
                        <CodeEditor
                            v-if="exampleChanges?.query !== undefined"
                            v-model="exampleChanges.query"
                        />
                    </div>
                </Fieldset>
                <Fieldset legend="Description">
                    <p>Providing a description helps the specialist agent know when and in what cases this examples is useful.</p>
                    <div>
                        <CodeEditor
                            v-if="exampleChanges?.notes !== undefined"
                            v-model="exampleChanges.notes"
                        />
                    </div>
                </Fieldset>
                <Fieldset legend="Code">
                    <p>Code given for a specific example helps the specialist agent use a known-working approach to handle the user's request.</p>
                    <div>
                        <CodeEditor
                            v-if="exampleChanges?.code !== undefined"
                            v-model="exampleChanges.code"
                            language="python"
                        />
                    </div>
                </Fieldset>
            </div>
            <div class="example-editor-button-container">
                <div class="example-buttons-left">
                    <Button
                        icon="pi pi-check-circle"
                        @click="saveExample(panelState.focusedExample)"
                        label="Apply Changes"
                        style="width: fit-content;"
                        severity="success"
                    />
                </div>
            </div>
        </div>
    </div>
</template>


<script setup lang="ts">

import { ref, nextTick, defineEmits, defineModel, defineProps, computed } from 'vue';
import Fieldset from 'primevue/fieldset';
import Button from "primevue/button";
import Divider from 'primevue/divider';
import Card from 'primevue/card';
import InputGroup from "primevue/inputgroup";
import InputGroupAddon from "primevue/inputgroupaddon";
import InputText from "primevue/inputtext";
import CodeEditor from '../misc/CodeEditor.vue';
import { type Example } from '../../util/integration'

type ExamplePanelState =
    | { view: "tableOfContents" }
    | { view: "focused", focusedExample: number }

const emit = defineEmits(['onUnsavedChange'])
const props = defineProps<{
    disabled?: boolean
}>()

const panelState = ref<ExamplePanelState>({view: 'tableOfContents'})
const selectedIntegration = defineModel<{examples?: Example[]}>()
const exampleChanges = ref<Example>(undefined);
const searchText = ref<string>();
const hoveredExample = ref<number|undefined>(undefined)

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

const newExample = () => {
    let examples = selectedIntegration.value?.examples;

    if (examples === undefined || examples === null) {
        selectedIntegration.value.examples = [];
        examples = selectedIntegration.value.examples;
    }

    examples.unshift({
        query: 'New Example',
        notes: '',
        code:  ''
    })
    exampleChanges.value = { ...examples[0] }
    panelState.value = { view: 'focused', focusedExample: 0 }
}

const editExample = (index) => {
    hoveredExample.value = undefined;
    let examples = selectedIntegration.value?.examples;
    exampleChanges.value = {
        notes: '',
        ...examples?.[index]
    }
    panelState.value = { view: 'focused', focusedExample: index }
}

const saveExample = (index) => {
    let examples = selectedIntegration.value?.examples;
    examples[index] = exampleChanges.value;
    exampleChanges.value = undefined;
    panelState.value = { view: 'tableOfContents' }
    emit('onUnsavedChange')
}

const deleteExample = (index) => {
    let examples = selectedIntegration.value?.examples;
    examples.splice(index, 1);
    panelState.value = { view: 'tableOfContents' }
    emit('onUnsavedChange')
}

</script>

<style lang="scss">

.header-controls {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.examples-panel {
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

.examples-editor-list {
    display: flex;
    flex-direction: column;
    overflow: auto;
    // top card box shadow
    padding: 0.2rem;
    div.p-card .p-card-content {
        padding: 0;
    }
    div.p-card-body {
        padding: 0.75rem 0.75rem;
    }
    div.p-card .p-card-title {
        margin-bottom: 0;
    }
    .example-caption {
        margin-top: 0.5rem;
        white-space: pre-wrap;
    }
    .example-card > div {
        margin-bottom: 0.5rem;;
    }
}

.example-arrow {
    transition: opacity 150ms linear;
    margin: auto 0;
}

.example-editor-focused {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    height: 100%;

    .example-editor-button-container {
        flex: 0 0;
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
        .example-buttons-left {
            button {
                margin-right: 0.5rem;
            }
        }
        .example-buttons-right {
            button {
                margin-left: 0.5rem;
            }
        }
    }

    .example-editor-main-content {
        flex: 1 1;
        p, ul, li {
            margin-bottom: 0.8rem;
            margin-top: 0rem;
        }
        > *:nth-child(1) {
            margin-top: 0rem;
        }
        font-size: 0.8rem;
        display: flex;
        overflow: auto;

        .v-codemirror {
            font-size: 0.8rem;
        }
    }
}

.example-editor-card-title {
    display: flex;
    flex-direction: row;
    .example-editor-card-title-text {
        flex: 1 1;
        font-size: 1rem;
        margin: auto;
        margin-left: 0;
        font-weight: 500;
    }
}


// for inner h1 being larger than header; rescale to make sensible whitespace

</style>
