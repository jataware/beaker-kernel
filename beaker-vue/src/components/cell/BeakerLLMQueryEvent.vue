<template>
    <div class="llm-query-event">
        <span v-if="isMarkdownRef" v-html="markdownBody" />
        <span v-if="props.event?.type === 'response' && parentQueryCell?.children?.length !== 0">
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
                                <span :class="chooseOutputIcon(child?.outputs)"/>
                                <span class="font-bold white-space-nowrap">{{ formatOutputs(child?.outputs, ["execute_result"]) }}</span>
                            </span>
                        </template>
                    <BeakerCodecellOutput :outputs="child?.outputs" />
                </AccordionTab>
            </Accordion>
        </span>
        <span v-else-if="props.event?.type === 'code_cell'">
            <BeakerCodeCell
                @click="notebook.selectCell(props.event?.content.cell_id)"
                :cell="getCellModelById(props?.event.content.cell_id)"
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
import { BeakerQueryEvent, BeakerQueryEventType, IBeakerCell } from "beaker-kernel/dist/notebook";
import { marked } from 'marked';
import BeakerCodeCell from "./BeakerCodeCell.vue";
import BeakerCodecellOutput from "./BeakerCodeCellOutput.vue";
import Accordion from "primevue/accordion";
import AccordionTab from "primevue/accordiontab";

import { BeakerNotebookComponentType } from '@/components/notebook/BeakerNotebook.vue';

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

const getCellModelById = (id): IBeakerCell | undefined => {
    for (const cell of notebook.notebook.cells) {
        const target = (cell.children as IBeakerCell | undefined)?.find(
            child => child.id === id
        );
        if (typeof target !== "undefined") {
            return target;
        }
    }
    return undefined;
}

const isMarkdown = (event: BeakerQueryEvent) => {
    const markdownTypes: BeakerQueryEventType[] = ["thought", "response", "user_answer", "user_question"];
    return markdownTypes.includes(event.type);
}

const isMarkdownRef = computed(() => isMarkdown(props.event))

const markdownBody = computed(() =>
    isMarkdown(props.event) ? marked.parse(props.event.content) : "");

type OutputType = "stream" | "error" | "execute_result" | "display_data";


const formatStream = (output, shortened: boolean): string => {
    return shortened ? output.name : `stream: ${output.name}`;
}

const formatError = (output, shortened: boolean): string => {
    return shortened ? output?.ename : `${output?.ename}: ${output?.evalue}`;
}

const formatExecuteResult = (output, shortened: boolean): string => {
    const values = Object.keys(output?.data || {});
    const userFacingNames = {
        "text/plain": "Text",
        "image/png": "Image"
    };
    const result = values.sort().map(
        (format) => Object.keys(userFacingNames)
            .includes(format) ? userFacingNames[format] : format)
            .join(", ");
    return shortened ? result.split(",")[0] : result;
}

const formatOutputs = (outputs: {output_type: OutputType}[], shorten: OutputType[]): string => {
    const formatters: {[key in OutputType]: (output: object, shortened: boolean) => string} = {
        "stream": formatStream,
        "error": formatError,
        "execute_result": formatExecuteResult,
        "display_data": formatExecuteResult
    };
    const headers: string[] = outputs.map(output =>
        formatters[output.output_type](output, shorten.includes(output.output_type)));
    return headers.join(", ");
}

// get the most meaningful icon for an execute_result; e.g. plaintext is less than image/png
const executeResultIcon = (output) => {
    const outputTypeIconMap = {
        "image/png": "pi pi-chart-bar",
        "text/html": "pi pi-table",
        "text/plain": "pi pi-align-left",
        "": "pi pi-code",
    };
    const precedenceList = ["image/png", "text/html", "text/plain"];
    const values = Object.keys(output?.data || {});
    for (const desiredType of precedenceList) {
        if (values.includes(desiredType)) {
            return outputTypeIconMap[desiredType];
        }
    }
    return ""
};

const chooseOutputIcon = (outputs: {output_type: OutputType}[]) => {
    const outputTypes = outputs.map(output => output.output_type);

    const result = outputs.find(output =>
        output.output_type === "execute_result"
        || output.output_type === "display_data");
    if (result !== undefined) {
        return executeResultIcon(result);
    }

    if (outputTypes.includes("error")) {
        return "pi pi-times-circle"
    }

    return "pi pi-pen-to-square"
}

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

/*
.agent-response-content .code-cell-output > div > div > .mime-select-container {
    justify-content: flex-start
}
*/


.agent-outputs {
    font-weight: 400;
    margin-bottom: 0rem;
    font-size: 1.1rem;
}

.agent-response-icon {

}

</style>
