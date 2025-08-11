<template>
    <div>
        <div class="mime-select-container" v-if="!(props.collapse && sortedMimetypes.length === 1)">
              <SelectButton
                  :allowEmpty="false"
                  v-model="selectedMimeType"
                  :options="sortedMimetypes"
              />
        </div>
        <div class="mime-payload">
            <component
                v-if="renderedBundle[selectedMimeType]?.component"
                :is="renderedBundle[selectedMimeType].component"
                v-bind="renderedBundle[selectedMimeType].bindMapping"
                :class="`rendered-output ${selectedMimeType.replace('/', '-')}`"
                @click="handleImageClick"
            />
        </div>

    </div>

</template>

<script lang="ts" setup>
import { ref, inject, computed, watch } from "vue";
import { useDialog } from "primevue";
import SelectButton from "primevue/selectbutton";
import { BeakerSession } from "beaker-kernel";
import type { BeakerRenderOutput } from "../../renderers";
import ImageZoomDialog from "./ImageZoomDialog.vue";

const props = defineProps([
    "mimeBundle",
    "collapse",
]);

const session = inject<BeakerSession>('session');

const dialog = useDialog();
const overlay = ref();

const renderedBundle = computed<{[key: string]: BeakerRenderOutput}>(
    () => {
        return session.renderer.renderMimeBundle(props.mimeBundle) as any as {[key: string]: BeakerRenderOutput}
    }
);
const sortedMimetypes = computed(() => {
    // Only display mimetypes in list that have a valid rendered payload
    return session.renderer.rankedMimetypesInBundle(props.mimeBundle).filter((obj) => {
        return Boolean(renderedBundle.value[obj]);
    })
});

const selectedMimeType = ref<string>(sortedMimetypes.value[0]);

// selectedMimeType needs to fulfill two things:
//   - user-selectable and not constantly computed
//   - but pick the most-relevant sorted mimetype when the bundle changes
// given that it's a ref the user can pick that needs to recompute on changed bundle,
// without this watcher, BeakerMimeBundles that don't unmount will ignore sorted types
watch(sortedMimetypes, (newSortedTypes, _) => {
    selectedMimeType.value = newSortedTypes[0];
})

// click-to-zoom for img tags
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
.p-accordion .p-accordion-header .p-accordion-header-link {
    background: var(--p-surface-a);
}

.mime-select-container {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem
}

.p-selectbutton .p-button.p-highlight {
    background: var(--p-surface-a);
    border: 3px solid var(--p-gray-300);
    color: var(--p-primary-text-color);
}

.p-selectbutton .p-button.p-highlight::before {
    box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, 0.02), 0px 1px 2px 0px rgba(0, 0, 0, 0.04);
}

.p-selectbutton .p-button {
    background: var(--p-gray-300);
    border: 1px solid var(--p-gray-300);
    color: var(--p-text-color-secondary);
    transition: background-color 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, outline-color 0.2s;
    height: 2rem;
    font-size: 0.75rem;
}

.preview-image {
    width: 100%;
}

.rendered-output {
    &.text-plain div {
        pre {
            display: inline-block;
            font-size: 0.75rem;
        }
    }
    &.text-html div.jp-RenderedHTML {
        div {
            overflow-x: auto;
        }
    }
    overflow-x: auto;

    &.image-png,
    &.image-jpeg,
    &.image-jpg,
    &.image-gif,
    &.image-svg {
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
}

.mime-payload {
    overflow-x: auto;
    display: flex;
    flex-direction: column
}
</style>
