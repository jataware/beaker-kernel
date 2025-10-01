<template>
    <div class="workflow-container">
        <p v-if="!attachedWorkflow">
            No workflow selected. Select one above or ask the agent about which workflow could work for your task.
        </p>
        <div class="final-response p-steppanel" v-html="finalResponse" @click="handleImageClick">

        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, inject, ref } from "vue";
import type { BeakerSessionComponentType } from '../session/BeakerSession.vue';
import { useWorkflows } from '../../composables/useWorkflows';
import { marked } from "marked";
import { ImageZoomDialog } from "../render";
import { useDialog } from "primevue";

const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
const { attachedWorkflow, attachedWorkflowFinalResponse } = useWorkflows(beakerSession);

const finalResponse = computed(() => {
    let response = `${attachedWorkflowFinalResponse.value}`;
    if (response === "") {
        response = "### No workflow output yet\nThis panel will be populated as the workflow stages complete."
    }
    response = response.split('\n').filter(line => !line.match(/^[|\s]+$/)).join('\n');
    return marked.parse(response)
})

const dialog = useDialog();
const overlay = ref();
const handleImageClick = (event: MouseEvent) => {
    const target = event.target as HTMLElement;
    if (target.tagName.toLowerCase() === 'img') {
        event.preventDefault();
        event.stopPropagation();
        const img = target as HTMLImageElement;
        overlay.value = dialog.open(
            ImageZoomDialog,
            {
                // Data used within the dialog to render the image.
                data: {
                    imageSrc: img.src,
                    imageAlt: img.alt || 'Zoomed image',
                },
                props: {
                    modal: true,
                    draggable: false,
                    showHeader: false,
                    closeButtonProps: {
                        class: "my-close-props",
                    },
                    style: {
                        width: "95vw",
                        maxHeight: "calc(95vh - 3rem)",
                        height: "100%",
                        position: "relative",
                        top: "1.5rem",
                    },
                    contentStyle: {
                        display: "flex",
                        flex: "1",
                        padding: "var(--p-overlay-modal-padding)",
                    }
                }
            }
        );
    }
};

</script>

<style lang="scss">

.final-response {
    h1 { font-size: 1.3rem; }
    h2 { font-size: 1.2rem; }
    h3 { font-size: 1.10rem; }
    h4 { font-size: 1.05rem; }
    br,hr { width: 100%; }
    padding: 0.5rem;

    table {
        table-layout: fixed;
        margin: 0 auto;
        border-collapse: collapse;
        border: 1px solid var(--p-datatable-body-cell-border-color);
        tbody tr:nth-child(odd) {
            background-color: var(--p-datatable-row-background);
        }
        tbody tr:nth-child(odd) {
            background-color: var(--p-datatable-row-striped-background);
        }
    }

    th,
    td {
        padding: 0.2rem;
        border: 1px solid var(--p-datatable-body-cell-border-color);
    }

    img {
        border-radius: 0.25rem;
        max-width: 100%;
        cursor: pointer;
        transition: box-shadow 0.6s ease;
        padding: 1px;

        &:hover {
            box-sizing: border-box;
            box-shadow: inset 0 0 0 1px var(--p-surface-500);
        }
    }
}

</style>
