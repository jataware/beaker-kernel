<template>
    <Accordion v-if="props.previewData" multiple :activeIndex="[0]">
        <AccordionTab v-for="itemMap, previewType of props.previewData" :key="previewType" :header="previewType">
            <div v-for="item, name of itemMap" :key="name">
                <h3>{{ name }}</h3>
                <BeakerMimeBundle :mimeBundle="item"/>
            </div>
        </AccordionTab>
    </Accordion>
    <div v-else>No preview yet</div>
</template>

<script lang="ts" setup>
import { ref, defineProps } from "vue";
import Accordion from 'primevue/accordion';
import AccordionTab from 'primevue/accordiontab';
import BeakerMimeBundle from "./BeakerMimeBundle.vue";

const props = defineProps([
    "previewData"
]);

// import DataTable from 'primevue/datatable';
// import Column from 'primevue/column';
// import SelectButton from 'primevue/selectbutton';
// import Card from 'primevue/card';

// const previewOneMockValue = ref('PNG');
// const previewOneMimeTypes = ref(['PNG', 'LATEX']);


// const products = [
// {
//     id: '1000',
//     name: 'Bamboo Watch',
//     description: 'Product Description',
//     price: 65,
//     category: 'Accessories',
//     quantity: 24,
//     inventoryStatus: 'INSTOCK',
//     rating: 5
// },
// {
//     id: '1000',
//     name: 'Bamboo Watch',
//     description: 'Product Description',
//     price: 65,
//     category: 'Accessories',
//     quantity: 24,
//     inventoryStatus: 'INSTOCK',
//     rating: 5
// }];
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
</style>
