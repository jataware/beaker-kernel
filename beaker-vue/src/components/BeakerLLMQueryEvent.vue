<template>
    <div class="llm-query-event">
        <span v-if="isMarkdownRef" v-html="markdownBody" />
        <span v-if="event.type === 'response'">
            <Accordion :multiple="true">
                <AccordionTab 
                    v-for="[index, child] in queryCell?.children?.entries()" 
                    :key="index"
                    :header="`${tabHeader(child?.outputs)}`"
                >
                    <BeakerCodecellOutput :outputs="child?.outputs" />
                </AccordionTab>
            </Accordion>
        </span>
        <span v-else-if="props.event?.type === 'code_cell'">
            <BeakerCodecell
                :cell="event.content.cell"
                :index="`${index}:${event.content.metadata.subindex}`"
                :class="{
                    selected: (index.toString() === selectedCellIndex),
                    'query-event-code-cell': true
                }"
                :selectedCellIndex="selectedCellIndex"
                @click.stop="selectCell(`${index}:${event.content.metadata.subindex}`)"
                :childOnClickCallback="selectCell"
            />
        </span>
    </div>
</template>

<script setup lang="ts">
import { defineProps, defineExpose, inject, onBeforeMount, computed, shallowRef } from "vue";
import { BeakerSession } from 'beaker-kernel';
import { BeakerQueryEvent, BeakerQueryEventType } from "beaker-kernel/dist/notebook";
import { marked } from 'marked';
import BeakerCodecell from "./BeakerCodecell.vue";
import BeakerCodecellOutput from "./BeakerCodecellOutput.vue";
import Accordion from "primevue/accordion";
import AccordionTab from "primevue/accordiontab";

const session: BeakerSession = inject("session");

const {
    selectCell,
    selectedCellIndex,
    runCell, 
    selectNextCell,
    getCell
}: any = inject("notebookCellExports")


const props = defineProps([
    'event',
    'index',
    'queryCell'
]);

onBeforeMount(() => {
    marked.setOptions({
       gfm: true,
       sanitize: false,
       langPrefix: `language-`,
     });
})

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
    return Object.keys(outputs[0].data);
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
