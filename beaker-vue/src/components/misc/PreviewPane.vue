<template>
    <Accordion 
        v-if="props.previewData" 
        multiple 
        :activeIndex="[...Array(props.previewData.length).keys()]"
        class="preview-accordion"
    >
        <AccordionTab 
            v-for="(itemMap, previewType) in props.previewData" 
            :key="previewType" 
            :header="previewType.toString()"
            class="preview-accordion-tab"
        >
            <Fieldset
                class="preview-container"
                v-for="(item, name) in Object.fromEntries(
                    Object.entries(itemMap).map(([_name, _item]) => {
                        const {'text/plain': _, ...significantBundle} = _item;
                        return [_name, significantBundle];
                    })
                )"
                :key="name"
                :legend="name.toString()"
                :toggleable="true"
            >
                <div 
                    v-html="item['text/html']" 
                    v-if="item && item['text/html'] !== undefined"
                    class="code-cell-output preview-container-table-wrapper"  
                />
                <MimeBundle v-else class="contextpreview-mime-bundle" :mimeBundle="item"/>
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

    overflow: auto;
    width: 100%;
    height: 100%;
}

.contextpreview-mime-bundle  {
    overflow: auto;
    height: 100%;
    > .mime-select-container {
        display: none;
    }
    > .mime-payload img {
        width: 100%;
    }
}

div.preview-container-table-wrapper {
    display: grid;
    grid-template-columns: repeat(1, minmax(0, 1fr));
    overflow: auto;
    white-space: normal;
}

.preview-accordion {
    div.p-accordion-content {
        padding: 1.25rem 0.3rem 1.25rem 0rem;
        .p-fieldset-content {
            padding: 1.25rem 0 1.25rem 0;
        }
    }
}
</style>
