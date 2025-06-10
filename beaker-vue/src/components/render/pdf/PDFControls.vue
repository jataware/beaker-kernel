<template>
    <div ref="controlsContainer" class="controls-container">
        <Toolbar>
            <template #start>
                <Button
                    class="pdf-ui-button"
                    icon="pi pi-chevron-left"
                    @click="emit('pdf-page-prev')"
                    :disabled="isLoading"
                />
                <Button
                    class="pdf-ui-button"
                    icon="pi pi-chevron-right"
                    @click="emit('pdf-page-next')"
                    :disabled="isLoading"
                />
                <InputGroup class="pdf-ui-inputselection">
                    <InputGroupAddon>
                        <i class="pi pi-book"></i>
                    </InputGroupAddon>
                    <InputText placeholder="Page" :value="props?.page"/>
                </InputGroup>
            </template>

            <template #center>
                <Button
                    class="pdf-ui-button"
                    icon="pi pi-search-minus"
                    @click="emit('pdf-zoom-out')"
                />
                <Button
                    class="pdf-ui-button"
                    icon="pi pi-search-plus"
                    @click="emit('pdf-zoom-in')"
                />
                <InputGroup class="pdf-ui-inputselection">
                    <InputGroupAddon>
                        <i class="pi pi-search"></i>
                    </InputGroupAddon>
                    <InputText placeholder="Zoom" :value="scaleToPercent(props?.scale)"/>
                </InputGroup>
            </template>
        </Toolbar>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import Toolbar from 'primevue/toolbar';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputGroup from 'primevue/inputgroup';
import InputGroupAddon from 'primevue/inputgroupaddon';

const props = defineProps([
    "page",
    "scale",
    "isLoading",
    "sidebarCallback"
])

const emit = defineEmits([
    "pdf-page-next",
    "pdf-page-prev",
    "pdf-zoom-in",
    "pdf-zoom-out"
])

const controlsContainer = ref(null);

const scaleToPercent = scale => `${Math.floor(scale * 100)}%`

</script>

<style scoped>
div.controls-container {
    div.p-toolbar {
        padding: 0.5rem;
        padding-left: 0.25rem;
    }
}

button.pdf-ui-button {
    padding: unset;
    margin: unset;
    margin-left: 0.25rem;
    margin-right: 0.25rem;
    height: 2rem;
    min-width: 2rem;
}

button.pdf-ui-button.pdf-ui-close {
    width: 2rem;
}

div.pdf-ui-inputselection {
    padding: unset;
    margin: unset;
    margin-left: 0.25rem;
    margin-right: 0.25rem;
    height: 2rem;
    div {
        min-width: 2rem;
        padding: 0;
    }
    input {
        width: 3rem;
    }
}
</style>
