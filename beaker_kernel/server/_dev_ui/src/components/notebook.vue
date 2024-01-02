<template>
    <div>
        <h1>Notebook. There should be cells below.</h1>
        <div>Imagine this is a toolbar.</div>
        <div id="cell-container">
            <CodeCell v-for="cell of session?.notebook?.cells" :content="cell"/>
        </div>
        <div>{{ session }}</div>
        <div>notebook: {{ session?.notebook }}</div>
        <div>_notebookModel: {{ session?._notebookModel }}</div>
        <div @click="addCell">add cell</div>

    </div>
</template>

<!-- // <script setup> -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { BeakerSession } from 'beaker-kernel';

import CodeCell from './codecell.vue'

// const cells = ref(["Hello world", "something else", "cell 3"]);

// const baseUrl = PageConfig.getBaseUrl();
const session = ref(null);

const addCell = () => {
    session.value.addCodeCell("Hello World!");
}

onMounted(() => {
    var beakerSession = new BeakerSession(
        {
            settings: {},
            name: "MyKernel",
            kernelName: "beaker"
        }
    );
    console.log('beakerSession', beakerSession);
    session.value = beakerSession;
})

</script>


<style>

</style>
