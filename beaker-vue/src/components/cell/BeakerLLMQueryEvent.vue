<template>
    <div class="llm-query-event">
        <span v-if="isMarkdownRef" v-html="markdownBody" />
        <span v-if="event.type === 'response'">
            <Accordion :multiple="true">
                <AccordionTab 
                    v-for="[index, child] in parentQueryCell?.children?.entries()" 
                    :key="index"
                    :header="`${tabHeader(child?.outputs)}`"
                >
                    <BeakerCodecellOutput :outputs="child?.outputs" />
                </AccordionTab>
            </Accordion>
        </span>
        <span v-else-if="props.event?.type === 'code_cell'">
            <BeakerCodeCell
                @click="notebook.selectCell(event.content.cell)"
                :cell="event.content.cell"
                :drag-enabled="false"
                :class="{
                    selected: (parentIndex.toString() === notebook.selectedCellId),
                    'query-event-code-cell': true
                }"
            />
        </span>
        <span v-else-if="props.event?.type === 'error'">
            <span>{{ `${event.content.ename}: ${event.content.evalue}` }}</span>
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

const parentIndex = computed(() => 
    notebook.notebook.cells.indexOf(props.parentQueryCell.value));

const isMarkdown = (event: BeakerQueryEvent) => {
    const markdownTypes: BeakerQueryEventType[] = ["thought", "response", "user_answer", "user_question"];
    return markdownTypes.includes(event.type);
}

const isMarkdownRef = computed(() => isMarkdown(props.event))

const markdownBody = computed(() => 
    isMarkdown(props.event) ? marked.parse(props.event.content) : "");

const tabHeader = (outputs) => {
    console.log(outputs);
    if (typeof outputs === "undefined") {
        return "";
    }
    return Object.keys(outputs[0]?.data || {});
}

function execute() {
    //const future = props.cell.execute(session);
}

defineExpose({execute});

</script>

<style lang="scss">

.query-event-code-cell {
    font-size: 0.75rem;
}

</style>