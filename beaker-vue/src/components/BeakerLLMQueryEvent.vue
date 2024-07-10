<template>
    <div class="llm-query-event">
        <span v-if="isMarkdownRef" v-html="markdownBody" />
        <span v-else-if="props.event?.type === 'code_cell'">
            <BeakerCodecell
                :cell="event.content.cell"
                :index="`${index}:${event.content.metadata.subindex}`"
                :class="{
                    selected: (index.toString() === selectedCellIndex),
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
import BeakerCell from "./BeakerCell.vue";

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
    'index'
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

function execute() {

    //const future = props.cell.execute(session);
}

defineExpose({execute});

</script>

<style lang="scss">

.markdown_cell + .user_question, .markdown_cell + .user_answer {
    background-color: var(--surface-b);
}

.user_question > div > p, .user_answer > div > p {
    padding: 0;
    margin: 0;
}

.user_answer {
    background-color: var(--surface-b);
}

.markdown_cell + .user_question {
    margin-bottom: 0;
    padding-bottom: 0;
}

div.events.markdown_cell.user_answer {
    margin-top: 0;
    padding-top: 0;
    margin-bottom: 0;
    border-radius: 0;
}

.events + .code_cell > span {
    width: 100%;
}

.user_answer {
    border-radius: 4px;
    background-color: var(--surface-c);
    padding: 0.4rem;
    display: inline-block;
    margin: 0.2rem 0;
}


span > div.markdown-cell {
    padding-left: 0;
}
</style>
