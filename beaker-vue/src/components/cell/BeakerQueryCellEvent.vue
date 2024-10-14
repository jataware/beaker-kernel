<template>
    <div class="llm-query-event">
        <span v-if="isMarkdown(event) && isValidResponse(event)" v-html="markdownBody" />
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
        <div v-else-if="props.event?.type === 'thought'">
            <div v-html="marked.parse(props.event.content.thought)" />
            <div v-if="props.event.content.background_code_executions.length">
                <Accordion :multiple="true" :active-index="[]">
                    <AccordionTab
                        v-for="(code_execution, index) in event.content.background_code_executions"
                        :key="`code_execution_${index}`"
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
                            <span class="flex align-items-center gap-2 w-full" style="font-weight: normal">
                                <span class="pi pi-icon pi-server"></span>
                                <span>Background Execution by Agent</span>
                            </span>
                        </template>
                        <div
                            class="monospace pre"
                            style="border: 1px var(--surface-border) solid; background-color: var(--surface-50); padding: 0.5rem"
                        >
                            {{ code_execution.code.trim() }}
                        </div>
                        <div v-if="code_execution.status === 'ok'">
                            <span class="pi pi-icon pi-check"></span>
                            Ran successfully
                        </div>
                        <div v-else>
                            <span class="pi pi-icon pi-exclamation-triangle"></span>
                            {{ capitalize(code_execution.status) }}
                            <div v-if="code_execution.status === 'error'">
                                <div>
                                {{ code_execution.ename }}: {{ code_execution.evalue }}
                                </div>
                                <div class="monospace pre">
                                    {{ stripAnsi(code_execution.traceback.join('\n').trim())}}
                                </div>
                            </div>
                        </div>
                    </AccordionTab>
                </Accordion>

            </div>
        </div>
        <span v-else-if="props.event?.type === 'code_cell'">
            <BeakerCodeCell
                @click="codeCellOnClick"
                :cell="getCellModelById(props?.event.content.cell_id)"
                :drag-enabled="false"
                :class="{
                    selected: isCodeCellSelected,
                    'query-event-code-cell': true
                }"
                :hide-output="true"
                ref="codeCellRef"
                v-keybindings="{
                    'keydown.enter.ctrl.prevent.capture.in-editor': (evt) => {
                        codeCellRef.execute();
                    },
                    'keydown.enter.shift.prevent.capture.in-editor': (evt) => {
                        codeCellRef.execute();
                    }
                }"
            />
            <span class="output-hide-text">(Output hidden -- shown in full response below.)</span>
        </span>
        <span v-else-if="props.event?.type === 'error'">
            <div>
                <pre class="pre" v-if="props?.event.content.ename">
                    {{props?.event.content.ename}}
                </pre>
                <pre class="pre" v-if="props?.event.content.evalue">
                    {{props?.event.content.evalue}}
                </pre>
                <Accordion>
                    <AccordionTab
                        :pt="{
                            header: {
                                class: [`agent-response-header`]
                            },
                            headerAction: {
                                class: [`agent-response-headeraction`]
                            },
                            content: {
                                class: [`agent-response-content`, 'agent-response-content-error']
                            },
                            headerIcon: {
                                class: [`agent-response-icon`]
                            }
                        }"
                    >
                        <template #header>
                            <span class="flex align-items-center gap-2 w-full">
                                <span class="font-bold white-space-nowrap">Traceback:</span>
                            </span>
                        </template>
                        <pre class="pre" v-if="props?.event.content.traceback">
                            {{props?.event.content.traceback?.join('\n')}}
                        </pre>
                    </AccordionTab>
                </Accordion>
            </div>
        </span>
    </div>
</template>

<script setup lang="ts">
import { defineProps, defineExpose, inject, onBeforeMount, computed, ref, capitalize } from "vue";
import { BeakerQueryEvent, type BeakerQueryEventType, type IBeakerCell } from "beaker-kernel/src/notebook";
import { marked } from 'marked';
import BeakerCodeCell from "./BeakerCodeCell.vue";
import BeakerCodecellOutput from "./BeakerCodeCellOutput.vue";
import Accordion from "primevue/accordion";
import AccordionTab from "primevue/accordiontab";
import stripAnsi from "strip-ansi";

import { BeakerSessionComponentType } from '../session/BeakerSession.vue';
import { BeakerNotebookComponentType } from '../notebook/BeakerNotebook.vue';


// use session where possible - notebook may or may not exist, but matters for selection!
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
const beakerNotebook = inject<BeakerNotebookComponentType>("notebook");
const codeCellRef = ref();

const props = defineProps([
    'event',
    'parentQueryCell',
]);

onBeforeMount(() => {
    marked.setOptions({
    //    gfm: true,
    //    sanitize: false,
    //    langPrefix: `language-`,
     });
})

// these need to be no-ops if notebook doesn't exist in the parent UI.
const codeCellOnClick = () => {
    if (beakerNotebook) {
        beakerNotebook.selectCell(props.event?.content.cell_id)
    }
}

// see above
const parentIndex = computed(() =>
    beakerSession.session.notebook.cells.indexOf(props.parentQueryCell.value));

const isCodeCellSelected = computed(() => {
    if (beakerNotebook) {
        return parentIndex.value.toString() === beakerNotebook.selectedCellId;
    }
    return false;
});

const lastOutput = computed(() => {
    if (props.parentQueryCell?.children?.length == 0) {
        return [0]
    }
    return [props.parentQueryCell?.children?.length - 1];
})

const getCellModelById = (id): IBeakerCell | undefined => {
    const notebook = beakerSession.session.notebook;
    for (const cell of notebook.cells) {
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
    const markdownTypes: BeakerQueryEventType[] = ["response", "user_answer", "user_question"];
    return markdownTypes.includes(event.type);
}

// if the agent response is 'None' rather than any plain text,
// we can assume that was the result of LOOP_SUCCESS returning None,
// in which case the side effect was the main desired output,
// and the agent 'None' can safely be ignored and hidden from the user.
const isValidResponse = (event: BeakerQueryEvent) => {
    if (event.type === "response" && event.content === "None") {
        return false;
    }
    return true;
}

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

defineExpose({
    execute,
});

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
    overflow-x: auto;
}

.agent-response-content-error pre {
    font-size: 0.7rem;
}


.agent-response-content .code-cell-output {
    background: none;
    border: none;
    padding: 0;
}

/* specifically within query cell outputs, make the width hand off to overflow */
/* note - this selector specifically matches the jupyter div, from inside the output,
   only in query cells. not needed anywhere else. preserves highlighting, etc. */
div.agent-response-content
div.code-cell-output
div
div.error
div
div
div
div.lm-Widget.jp-RenderedText.jp-mod-trusted {
    width: 1px;
    font-size: 0.7rem;
}


.agent-outputs {
    font-weight: 400;
    margin-bottom: 0rem;
    font-size: 1.1rem;
}

</style>
