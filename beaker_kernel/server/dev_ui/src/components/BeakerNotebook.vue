<template>
    <div>
        <h1>Notebook. There should be cells below.</h1>
        <div>Imagine this is a toolbar.</div>
        <div id="cell-container">
            <!-- <BeakerCodeCell v-for="cell of session?.notebook?.cells" :key="cell.id" :content="cell"/> -->
            <BeakerCodeCell v-for="cell of session?._notebookModel?.sharedModel?.cells" :key="cell.id" :content="cell"/>
        </div>
        <div>{{ session }}</div>
        <div>notebook: {{ session?.notebook }}</div>
        <div>_notebookModel: {{ session?._notebookModel }}</div>
        <div @click="addCell">add cell</div>

    </div>
</template>

<!-- // <script setup> -->
<script setup lang="ts">
import { ref, onMounted, defineProps, getCurrentInstance } from "vue";
import { BeakerSession } from 'beaker-kernel';

import BeakerCodeCell from './BeakerCodecell.vue'

const props = defineProps([
    "session", "foo"
])

// const cells = ref(["Hello world", "something else", "cell 3"]);

// const baseUrl = PageConfig.getBaseUrl();

// console.log(settings);
// const session = ref(
//     new BeakerSession(
//         {
//             settings: settings,
//             name: "MyKernel",
//             kernelName: "beaker"
//         }
//     )
// );


const addCell = () => {
    props.session.addCodeCell("Hello World!");
    let [cell] = props.session?._notebookModel?.sharedModel?.cells;
    console.log(cell);
    // const instance = getCurrentInstance();
    // console.log(instance);
    // instance?.proxy.forceUpdate();
    // props.session.proxy.forceUpdate();

}

// onMounted(() => {
//     console.log("mounted", session.value)
//     // console.log('beakerSession', beakerSession);
//     // session.value = beakerSession;
// })

</script>


<style>

</style>
