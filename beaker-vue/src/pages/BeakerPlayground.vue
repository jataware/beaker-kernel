<template>
    <div class="beaker-playground">
        <header>
            <nav>
                <ul>
                    <li>home</li>
                </ul>
            </nav>
        </header>

        <main
            @keydown="handleKeyboardShortcut"
        >
            <NotebookControls
                :selectCell="selectCell"
                :selectedCellIndex="selectedCellIndex"
                :runCell="runCell"
            />

            <Button text size="small" label="debug" @click="debug" />

            <Notebook
                :selectCell="selectCell"
                :selectedCellIndex="selectedCellIndex"
                ref="notebookRef"
            />

        </main>

        <aside>
        <!--
            <ContextSelection />
            -->
        </aside>
    </div>

</template>

<script setup lang="tsx">
import { ref, onBeforeMount, computed, provide, inject } from "vue";
import { BeakerSession } from 'beaker-kernel';
import Button from 'primevue/button';

import Notebook from './lib/UINotebook.vue';
import NotebookControls from './lib/UINotebookControls.vue';
// import ContextSelection from './lib/UIContextSelection.vue';

const session: BeakerSession = inject('session');

const cellCount = computed(() => session.notebook?.cells?.length || 0);

const selectedCellIndex = ref(0);
const activeContext = ref(undefined);
const notebookRef = ref(null);

provide('theme', 'light');

const selectCell = (index) => {
    selectedCellIndex.value = index;
}

function debug() {
    console.log('selectedCellIndex', selectedCellIndex.value);
}

function runCell() {
    notebookRef.value.executeSelectedCell();
}

function handleKeyboardShortcut(event) {

    const { target } = event;

    // TODO is there a better way to encapsulate cancelling events
    // when writing on textarea/input/code elements ?
    const isEditingCode = target.className === 'cm-content'; // codemirror
    // const isTextArea = target.className.includes('resizeable-textarea');

    if (isEditingCode) {
        return;
    }

    notebookRef.value.handleKeyboardShortcut(event);
}

onBeforeMount(() => {
    if (cellCount.value <= 0) {
        session.addCodeCell("");
        selectCell(0);
    }
});

</script>

<style lang="scss">
.beaker-playground {
    height: 100vh;
    width: 100vw;
    display: grid;
    grid-gap: 1rem;

    grid-template-areas:
        "header header"
        "main aside"
        "footer footer";

    grid-template-columns: 2fr 1fr;
    grid-template-rows: auto 1fr auto;
}

header {
    grid-area: header;
    display: flex;
    justify-content: space-between;
    align-items: center;
    li {
        display: inline;
        list-style: none;
        margin-right: 1rem;
    }
}

main {
    grid-area: main;
    display: flex;
    flex-direction: column;
    padding-left: 1rem;
}

aside {
    grid-area: aside;
}

footer {
    grid-area: footer;
}

</style>
