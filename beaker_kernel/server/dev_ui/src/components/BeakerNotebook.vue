<template>
    <div class="beaker-notebook">
        <h2>Your notebook:</h2>
        <div class="beaker-nb-toolbar">
            <span class="button btn" @click="addCell">add cell</span>
        </div>
        <div id="cell-container">
            <BeakerCodeCell
                v-for="cell of props.session?.notebook?.cells" :key="cell.id" :cell="cell"
                :session="props.session" v-model="foo"
            />
            <div>{{ props.session.notebook.toJSON() }}</div>
        </div>

    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, defineProps, computed } from "vue";
import { BeakerSession } from 'beaker-kernel';

import BeakerCodeCell from './BeakerCodecell.vue'

const props = defineProps([
    "session"
]);

const foo = ref("Hello world");

const addCell = () => {
    props.session.addCodeCell("");
    console.log(props.session.notebook);
}
</script>


<style>
.beaker-notebook {
    margin-left: 30%;
    margin-right: 30%;
}

.beaker-nb-toolbar {
    vertical-align: middle;
    background-color: #aaa;
    height: 4ex;
    padding-top: 1em;
}

.btn {
    border: gray 1px ;
    border-style: ridge;
    padding: 1ex;
}

</style>
