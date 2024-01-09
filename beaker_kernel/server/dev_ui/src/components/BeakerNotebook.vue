<template>
    <div class="beaker-notebook">
        <h2>Your notebook:</h2>
        <BeakerAgentQuery class="agent-query-container" :session="session" @select-cell="selectCell" @run-cell="runCell"/>
        <div class="beaker-nb-toolbar">
            <span class="btn" @click="addCell">add cell</span>
            <span class="btn" @click="removeCell">remove cell</span>
            <span class="btn" @click="runCell">run cell</span>
        </div>
        <div id="cell-container">
            <component
                v-for="(cell, index) in props.session?.notebook?.cells" :key="cell.id" :cell="cell"
                :is="componentMap[cell.cell_type]"
                :session="props.session" class="beaker-cell" :class="{selected: (index == selectedCellIndex)}"
                @click="selectCell(index)"
            />
            <div>{{ props.session.notebook.toJSON() }}</div>
        </div>

    </div>
</template>

<script setup lang="ts">
import { ref, onBeforeMount, onMounted, defineProps, computed } from "vue";
import { BeakerSession, IBeakerCell, BeakerBaseCell } from 'beaker-kernel';

import BeakerCodeCell from './BeakerCodecell.vue';
import BeakerLLMQueryCell from "./BeakerLLMQueryCell.vue";
import BeakerAgentQuery from './BeakerAgentQuery.vue';

const componentMap = {
    'code': BeakerCodeCell,
    'query': BeakerLLMQueryCell,
}

const props = defineProps([
    "session"
]);

const selectedCellIndex = ref(0);

const selectedCell = computed(() => {
    return _getCell(selectedCellIndex.value);
});

const _cellIndex = (cell: IBeakerCell): number => {
    let index = -1;
    if (cell instanceof BeakerBaseCell) {
        index = props.session.notebook.cells.indexOf(cell);
    }
    return index;
}

const _getCell = (cell: number | IBeakerCell) => {
    const index = _cellIndex(cell);
    return props.session.notebook.cells[index];
}


const selectCell = (cell: number | IBeakerCell) => {
    let index = -1;
    if (Number.isInteger(cell) ) {
        index = cell;
    }
    else if (cell instanceof BeakerBaseCell) {
        index = _cellIndex(cell);
    }
    selectedCellIndex.value = index;
}

const addCell = () => {
    props.session.addCodeCell("");
}

const runCell = (cell: number | IBeakerCell) => {
    if (cell) {
        cell = _getCell(cell);
    }
    else {
        cell = selectedCell.value;
    }
    if (cell !== undefined) {
        cell.execute(props.session);
    }
}

const removeCell = () => {
    props.session.notebook.removeCell(selectedCellIndex.value);
    // Always keep at least one cell. If we remove the last cell, replace it with a new empty codecell.
    if (props.session.notebook.cells.length == 0) {
        props.session.addCodeCell("");
    }
    // Fixup the selection if we remove the last item.
    if (selectedCellIndex.value <= props.session.notebook.cells.length) {
        selectedCellIndex.value = props.session.notebook.cells.length - 1;
    }
};

onBeforeMount(() => {
    if (props.session.notebook.cells.length <= 0) {
        props.session.addCodeCell("");
    }
});

</script>


<style>
.beaker-notebook {
    margin-left: 30%;
    margin-right: 30%;
    text-align: start;
}

.beaker-nb-toolbar {
    vertical-align: middle;
    background-color: #aaa;
    height: 4ex;
    padding-top: 1em;
}

#cell-container {
    border: solid 1px black;
    padding: 10px;
}

.beaker-cell {
    border: solid 1px lightgray;
}

.beaker-cell.selected {
    border: solid 1px black;
}

.agent-query-container {
    /* margin-bottom: 10px; */
    padding-left: 0.5em;
}

.btn {
    border: gray 1px ;
    border-style: ridge;
    padding: 1ex;
    cursor: pointer;
    margin: 0.5em;
}

</style>
