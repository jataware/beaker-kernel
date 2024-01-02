<template>
    <div class="code-cell">
        {{ props.content }}

        <CodeCellOutput />
    </div>
</template>

<script setup>
import CodeCellOutput from "./codecell-output.vue";

const props = defineProps(["content"]);


</script>


<style>
.code-cell {
    margin: 1em;
    padding: 1em;
    background-color: rosybrown;
}

</style>
