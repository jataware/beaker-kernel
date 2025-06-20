<template>
    <div class="code-cell-output" :class="{'code-cell-output-dropdown': props.dropdownLayout}">
        <div v-if="dropdownLayout">
            <div class="code-cell-output-box-dropdown">
                <Accordion>
                    <AccordionTab
                        class="code-cell-output-dropdown-tab"
                        :pt="{
                            header: {
                                class: [`code-cell-output-dropdown-header`]
                            },
                            headerAction: {
                                class: [`code-cell-output-dropdown-headeraction`]
                            },
                            content: {
                                class: [`code-cell-output-dropdown-content`]
                            },
                            headerIcon: {
                                class: [`code-cell-output-dropdown-icon`]
                            }
                        }"
                    >
                        <template #header>
                            <span class="flex align-items-center gap-2 w-full" style="font-weight: normal">

                                <span>Outputs</span>
                            </span>
                        </template>
                        <div
                            class="code-cell-dropdown-content"
                            v-for="output of props.outputs"
                            :key="`${output}-dropdown`"
                        >
                            <div
                                v-if="output.output_type == 'stream'"
                                :class="output.output_type"
                                v-html="ansiHtml(escapeHtml(output.text))"
                            />
                            <BeakerMimeBundle
                                v-else-if="['display_data', 'execute_result'].includes(output.output_type)"
                                :mime-bundle="output.data"
                                class="mime-bundle"
                                collapse="true"
                            />
                            <div v-else-if="output.output_type == 'error'" :class="output.output_type">
                                <BeakerMimeBundle :mime-bundle="rebundleError(output)" collapse="true" />
                            </div>
                            <div v-else>{{ output }}</div>
                        </div>
                    </AccordionTab>
                </Accordion>
            </div>
        </div>
        <div v-else>
            <div
                class="code-cell-output-box"
                :class="{'collapsed-output': output.metadata?.collapsed}"
                v-for="output of props.outputs"
                :key="output"
            >
                <div class="output-collapse-box" @click.capture.stop.prevent="collapseOutput(output)"></div>
                <div
                    v-if="output.output_type == 'stream'"
                    :class="output.output_type"
                    v-html="ansiHtml(escapeHtml(output.text))"
                />
                <BeakerMimeBundle
                    v-else-if="['display_data', 'execute_result'].includes(output.output_type)"
                    :mime-bundle="output.data"
                    class="mime-bundle"
                    collapse="true"
                />
                <div v-else-if="output.output_type == 'error'" :class="output.output_type">
                    <BeakerMimeBundle :mime-bundle="rebundleError(output)" collapse="true" />
                </div>
                <div v-else>{{ output }}</div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import BeakerMimeBundle from "../render/BeakerMimeBundle.vue";
import ansiHtml from "ansi-html-community";
import escapeHtml from "escape-html";
import Accordion from "primevue/accordion";
import AccordionTab from "primevue/accordiontab";

const props = defineProps([
    "outputs",
    "busy",
    "dropdownLayout"
]);

const collapseOutput = (output) => {
    const metadata = ref(output?.metadata || (output.metadata = {}))
    metadata.value.collapsed = !metadata.value.collapsed;
}

const rebundleError = (errorOutput) => {
    const traceback = (Array.isArray(errorOutput.traceback) ? errorOutput.traceback?.join('\n') : errorOutput.traceback?.toString());
    const bundle = {
        'application/vnd.jupyter.error':  errorOutput,
        'application/vnd.jupyter.stderr': traceback || `${errorOutput.ename}: ${errorOutput.evalue}`,
    }
    return bundle;
}

</script>


<style lang="scss">

.code-cell-output {
    --collapse-height: 3em;

    padding: 0 0.5em 0.5em 0;
    background-color: var(--p-surface-c);
    position: relative;
    .execute_result {
        pre {
            white-space: break-spaces;
            overflow-wrap: break-word;
        }
    }

    table {
        min-width: 75%;
        text-align: end;
        border-collapse: collapse;
        border-width: 1px;
        border-color: rgba(255,0,0,0.0);

        th, td {
            text-align: end;
            padding: 0.25rem 0.5rem;
            border-width: 1px;
        }

        th {
            font-weight: bold;
            background-color: var(--p-surface-b);

            &:hover {
                background-color: var(--p-surface-b);
                border: 1px solid var(--p-text-color);
            }
        }

        thead {
            text-align: start;
            background-color: var(--p-surface-b);
        }

        tbody {
            th {
                text-align: center;
            }

            tr {
                background-color: var(--p-surface-c);
            }
            tr:nth-child(even) {
                background-color: var(--p-surface-a);
            }

            td:hover {
                background-color: var(--p-surface-d) !important;
                border: 1px solid var(--p-text-color) !important;
            }
        }
    }
}

.mime-bundle {
    width: 100%;
}

.collapsed-output {
    max-height: var(--collapse-height);
    overflow-y: auto;

    .output-collapse-box {
        background-color: var(--p-surface-border);
    }
}

.code-cell-output-box {
    margin-top: 0.5em;
    display: flex;
    flex-direction: row;
    height: 100%;
}

.output-collapse-box {
    min-width: 10px;
    width: 10px;
    border: 1px inset var(--p-surface-border);
    cursor: pointer;

    &:hover {
        background-color: color(from var(--p-surface-border) srgb r g b / 0.5);
    }
    margin-right: 0.5em;

}

.stdout {
    // was dark purple and hard to see- replaced with theme colors
    color: var(--p-text-color-secondary);
    white-space: pre;
    font-style: italic;
}

.stream {
    white-space: pre-wrap;
}

.stderr {
    color: #a44; // seems unused
    white-space: pre;
}

.code-cell-output-dropdown {
    background: none;
}
.code-cell-output-dropdown-header {
    background: none;
    width: 100%;
}
.p-accordion .p-accordion-header a.code-cell-output-dropdown-headeraction {
    padding-left: 0px;
    background: none;
    border: none;
    padding-top: 1rem;
    padding-bottom: 0;
    svg {
        flex-shrink: 0;
    }
}
.code-cell-output-dropdown-content {
    font-size: 0.85rem;
    padding: 0px;
    padding-top: 1em;
    background: none;
    border: none;
}

</style>
