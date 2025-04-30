<template>
    <div class="llm-query-event">
        <div
            v-if="isMarkdown(event) && isValidResponse(event)"
            v-html="markdownBody"
            class="md-inline"
        />
        <div v-if="props.event?.type === 'response' && parentEntries !== 0">
            <!-- <h4 class="agent-outputs">Outputs:</h4> -->
            <Accordion :multiple="true" :active-index="meaningfulOutputs">
                <AccordionTab
                    v-for="[index, child] in filteredParentEntries"
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
                            <!-- <span :class="chooseOutputIcon(child?.outputs)"/>
                            <span class="font-bold white-space-nowrap">{{ formatOutputs(child?.outputs, ["execute_result"]) }}</span> -->
                            <span>Outputs</span>
                        </span>
                    </template>
                    <BeakerCodecellOutput :outputs="child?.outputs" />
                </AccordionTab>
            </Accordion>
        </div>
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
                            style="
                                border: 1px var(--surface-border) solid;
                                background-color: var(--surface-50);
                                padding: 0.5rem;
                                padding-top: 0rem;
                                margin-bottom: 0.5rem;
                                overflow: auto;
                            "
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
                                <div class="monospace pre" v-html="ansiHtml(code_execution.traceback.join('\n').trim())"/>
                            </div>
                        </div>
                    </AccordionTab>
                </Accordion>

            </div>
        </div>
        <span v-else-if="props.event?.type === 'code_cell'" style="position: relative;">
            <BeakerCodeCell
                @click="codeCellOnClick"
                :cell="getCellModelById(props?.event.content.cell_id)"
                :drag-enabled="false"
                :class="{
                    selected: isCodeCellSelected,
                    'query-event-code-cell': true,
                    'code-cell-collapsed': expandedCodeCell
                }"
                :hide-output="false"
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
            <Button 
                :icon="!expandedCodeCell ? 'pi pi-window-minimize' : 'pi pi-expand'" 
                size="small"
                class="code-cell-toggle-button" 
                @click.stop="toggleCodeCellExpansion"
                :title="!expandedCodeCell ? 'Shrink code cell' : 'Expand code cell'"
            />
            <!-- <span class="output-hide-text">(Output hidden -- shown in full response below.)</span> -->
        </span>
        <span v-else-if="props.event?.type === 'error' && props.event.content.ename === 'CancelledError'">
            <h4 class="p-error">Request cancelled.</h4>
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
import Button from "primevue/button";
import { BeakerQueryEvent, type BeakerQueryEventType, type IBeakerCell } from "beaker-kernel/src/notebook";
import { marked } from 'marked';
import BeakerCodeCell from "./BeakerCodeCell.vue";
import BeakerCodecellOutput from "./BeakerCodeCellOutput.vue";
import Accordion from "primevue/accordion";
import AccordionTab from "primevue/accordiontab";
import ansiHtml from "ansi-html-community";
import { formatOutputs, chooseOutputIcon } from './BeakerCodeCellOutputUtilities'
import { BeakerSessionComponentType } from '../session/BeakerSession.vue';
import { BeakerNotebookComponentType } from '../notebook/BeakerNotebook.vue';


// use session where possible - notebook may or may not exist, but matters for selection!
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
const beakerNotebook = inject<BeakerNotebookComponentType>("notebook");
const codeCellRef = ref();
const expandedCodeCell = ref(true);

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

const parentEntries = computed(() => {
    const isAllTextPlain = props.parentQueryCell?.children?.map((child =>
        child?.outputs?.every(output => {
            if (output?.data !== undefined) {
                const mimetypes = Object.keys(output?.data);
                // if only text/plain is returned
                return output?.output_type === 'execute_result'
                    && mimetypes.length === 1
                    && mimetypes[0] === 'text/plain';
            }
            else {
                return true;
            }
        // only handle cases where every single loop iteration returns only all text/plain
        // to not greedily handle longer agent requests
        }))).every(x => x);
    // omit the list going to vue to hide it
    return isAllTextPlain ? [] : props.parentQueryCell?.children?.entries();
});

const meaningfulOutputs = computed(() => {
    const outputs = [];
    props.parentQueryCell?.children?.entries()?.forEach(([index, child]) => {
        child?.outputs?.forEach(output => {
            const desiredOutputs = ['image/png', 'text/html'];
            const desiredTypes = ['execute_result', 'display_data'];
            if (
                desiredTypes.includes(output?.output_type)
                && desiredOutputs.map(value =>
                    (Object.keys(output?.data ?? [])).includes(value)).some(found => found))
            {
                outputs.push(index);
            }
        });
    });
    return outputs;
})

const toggleCodeCellExpansion = (event) => {
    event.stopPropagation(); // Prevent triggering the thought item click
    expandedCodeCell.value = !expandedCodeCell.value;
};

const hasOutputData = (child) => {
    if (!child || !child.outputs || child.outputs.length === 0) {
        return false;
    }
    
    // Check if any output has data that's not empty
    return child.outputs.some(output => 
        output.data && Object.keys(output.data).length > 0
    );
};

// TODO this worked, but I'd rather show a "no outputs" message if there are no outputs than hide it
// Create a filtered computed property
const filteredParentEntries = computed(() => {
    if (!parentEntries.value) return [];
    
    // Convert entries iterator to array and filter it
    const entriesArray = Array.from(parentEntries.value);
    return entriesArray.filter(([_, child]) => hasOutputData(child));
});

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
    isMarkdown(props.event) ? marked.parse(props.event.content, {async: false}).trim() : "");

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
    max-height: 35rem;
    overflow-y: auto;
}

.output-hide-text {
    font-size: 0.9rem;
    font-style: italic;
}

.agent-response-header {
    padding-left: 0px;
    background: none;
    border: none;
    padding-bottom: 0.5rem;
}

.p-accordion .p-accordion-header a.p-accordion-header-link.agent-response-headeraction  {
    padding-left: 0px;
    background: none;
    border: none;
    padding-top: 1rem;
    padding-bottom: 0;
    svg {
        flex-shrink: 0;
    }
}

a.agent-response-headeraction > span > span.pi {
    align-items: center;
    margin: auto;
    padding-right: 0.25rem;
}

.agent-response-content {
    padding-top: 0rem;
    background: none;
    border: none;
    div.mime-select-container {
        display:none;
    }
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

.md-inline {
    pre {
        overflow-x: auto;
        code {
            display: inline-block;
            // min-width: 100%;
            // width: 0px;
            font-size: 0.75rem;
        }
    }

    p:first-child {
        margin-top: 0.5rem;
    }
    p:last-child {
        margin-bottom: 0.5rem;
    }
}

.code-cell-collapsed {
  max-height: 200px;
  overflow-y: hidden;
  border: 1px solid var(--surface-border);
  border-radius: var(--border-radius);
  padding: 0.25rem;
}
.code-cell-toggle-button {
  position: absolute;
  bottom: 2rem;
  right: 3.5rem;
  margin: 0;
  padding: 0.5rem 0;
  background: #666666AA;
  border-color: #555555DD;
  &>.p-button-icon {
    font-weight: bold;
  }
}

</style>
