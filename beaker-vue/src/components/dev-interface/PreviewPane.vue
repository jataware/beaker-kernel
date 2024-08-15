<template>
    <Accordion v-if="props.previewData" multiple :activeIndex="[0]">
        <AccordionTab v-for="(itemMap, previewType) in props.previewData" :key="previewType" :header="previewType.toString()">
            <Fieldset
                class="preview-container"
                v-for="(item, name) in itemMap"
                :key="name"
                :legend="name.toString()"
                :toggleable="true"
            >
                <MimeBundle :mimeBundle="item"/>
            </Fieldset>
        </AccordionTab>
    </Accordion>
    <div v-else>No preview yet</div>
</template>

<script lang="ts" setup>
import { defineProps } from "vue";
import Accordion from 'primevue/accordion';
import AccordionTab from 'primevue/accordiontab';
import Fieldset from "primevue/fieldset";
import MimeBundle from "../render/BeakerMimeBundle.vue";

const props = defineProps<{
    previewData: {[key: string]: {[key: string]: {[key: string]: any}}}
}>();
</script>


<style lang="scss">
.p-accordion .p-accordion-header .p-accordion-header-link {
    background: var(--surface-a);
}

.mime-select-container {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem
}

.p-selectbutton .p-button.p-highlight {
    background: var(--surface-a);
    border: 3px solid var(--gray-300);
    color: var(--primary-text-color);
}

.p-selectbutton .p-button.p-highlight::before {
    box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, 0.02), 0px 1px 2px 0px rgba(0, 0, 0, 0.04);
}

.p-selectbutton .p-button {
    background: var(--gray-300);
    border: 1px solid var(--gray-300);
    color: var(--text-color-secondary);
    transition: background-color 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, outline-color 0.2s;
    height: 2rem;
    font-size: 0.75rem;
}

.preview-image {
    width: 100%;
}

.preview-container {
    margin-bottom: 1rlh;
    word-wrap: break-word;

    pre {
        white-space: pre-wrap;
    }
}
</style>
