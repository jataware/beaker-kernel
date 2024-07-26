<template>
    <div class="llm-query-event">
        <span v-if="isMarkdownRef" v-html="markdownBody" />
        <span v-if="props.event?.type === 'response'">
            <h4 class="agent-outputs">Outputs:</h4>
            <Accordion :multiple="true" :active-index="lastOutput">
                <AccordionTab 
                    v-for="[index, child] in parentQueryCell?.children?.entries()" 
                    :key="index"
                    :pt="{
                        header: {
                            class: [`agent-response-header`]
                        },
                        headerAction: {
                            class: [`agent-response-headeraction`]
                        },
                        content: {
                            class: [`agent-response-content`]
                        },
                        headerIcon: {
                            class: [`agent-response-icon`]
                        }
                    }"
                >
                        <template #header>
                            <span class="flex align-items-center gap-2 w-full">
                                <span :class="outputTypeIconMap[findMeaningfulTypeFromOutputs(child?.outputs)]"/>
                                <span class="font-bold white-space-nowrap">{{ tabHeaderShortened(child?.outputs) }}</span>
                            </span>
                        </template>
                    <BeakerCodecellOutput :outputs="child?.outputs" />
                </AccordionTab>
            </Accordion>
        </span>
        <span v-else-if="props.event?.type === 'code_cell'">
            <BeakerCodeCell
                @click="notebook.selectCell(props.event?.content.cell)"
                :cell="props?.event.content.cell"
                :drag-enabled="false"
                :class="{
                    selected: (parentIndex.toString() === notebook.selectedCellId),
                    'query-event-code-cell': true
                }"
                :hide-output="true"
            />
            <span class="output-hide-text">(Output hidden -- shown in full response below.)</span>
        </span>
        <span v-else-if="props.event?.type === 'error'">
            <span>{{ `${props?.event.content.ename}: ${props?.event.content.evalue}` }}</span>
        </span>
    </div>
</template>

<script setup lang="ts">
import { defineProps, defineExpose, inject, onBeforeMount, computed, shallowRef } from "vue";
import { BeakerSession } from 'beaker-kernel';
import { BeakerQueryEvent, BeakerQueryEventType } from "beaker-kernel/dist/notebook";
import { marked } from 'marked';
import BeakerCodeCell from "./BeakerCodeCell.vue";
import BeakerCodecellOutput from "./BeakerCodeCellOutput.vue";
import Accordion from "primevue/accordion";
import AccordionTab from "primevue/accordiontab";

import { BeakerNotebookComponentType } from '@/components/notebook/BeakerNotebook.vue';

const session: BeakerSession = inject("session");
const notebook = inject<BeakerNotebookComponentType>("notebook");

const props = defineProps([
    'event',
    'parentQueryCell',
]);

onBeforeMount(() => {
    marked.setOptions({
       gfm: true,
       sanitize: false,
       langPrefix: `language-`,
     });
})

const lastOutput = computed(() => {
    if (props.parentQueryCell?.children?.length == 0) {
        return [0]
    }
    return [props.parentQueryCell?.children?.length - 1];
})

const parentIndex = computed(() => 
    notebook.notebook.cells.indexOf(props.parentQueryCell.value));

const isMarkdown = (event: BeakerQueryEvent) => {
    const markdownTypes: BeakerQueryEventType[] = ["thought", "response", "user_answer", "user_question"];
    return markdownTypes.includes(event.type);
}

const isMarkdownRef = computed(() => isMarkdown(props.event))

const markdownBody = computed(() => 
    isMarkdown(props.event) ? marked.parse(props.event.content) : "");

const outputTypes = (outputs) : string[] => {
    if (typeof outputs === "undefined") {
        return [];
    }
    return Object.keys(outputs[0]?.data || {});
}

const tabHeader = (outputs) : string => {
    const values = outputTypes(outputs);
    const userFacingNames = {
        "text/plain": "Text",
        "image/png": "Image"
    };
    return values.sort().map(
        (format) => Object.keys(userFacingNames)
            .includes(format) ? userFacingNames[format] : format)
            .join(", ");
};

const tabHeaderShortened = (outputs) : string => {
    return tabHeader(outputs).split(",")[0];
}

// get the most meaningful icon for a given list of outputs; e.g. plaintext is less than image/png
const findMeaningfulTypeFromOutputs = (outputs) => {
    const precedenceList = ["image/png", "text/html", "text/plain"];
    const values = outputTypes(outputs);
    for (const desiredType of precedenceList) {
        if (values.includes(desiredType)) {
            return desiredType;
        }
    }
    return ""
};

const outputTypeIconMap = {
    "image/png": "pi pi-chart-bar",
    "text/html": "pi pi-table",
    "text/plain": "pi pi-align-left",
    "": "pi pi-code",
};


function execute() {
    //const future = props.cell.execute(session);
}

defineExpose({execute});

</script>

<style lang="scss">

.query-event-code-cell {
    font-size: 0.75rem;
    padding-top: 1rem;
    padding-bottom: 0.25rem;
}

.output-hide-text {
    font-size: 0.9rem;
    font-style: italic;
}

.agent-response-header {
    padding-left: 0px;
    background: none;
    border: none;
    padding-bottom: 0;
}

.p-accordion .p-accordion-header a.p-accordion-header-link.agent-response-headeraction  {
    padding-left: 0px;
    background: none;
    border: none;
    padding-top: 1rem;
    padding-bottom: 0;
}

a.agent-response-headeraction > span > span.pi {
    align-items: center;
    margin: auto; 
    padding-right: 0.25rem;
}

.agent-response-content {
    background: none;
    border: none;
}

.agent-response-content .code-cell-output {
    background: none;
    border: none;
    padding: 0;
}

.agent-response-content .code-cell-output > div > div > .mime-select-container {
    display:none
}


.agent-outputs {
    font-weight: 400;
    margin-bottom: 0rem;
    font-size: 1.1rem;
}

.agent-response-icon {

}

</style>