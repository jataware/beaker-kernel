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
            />
        </div>
    </div>

</template>

<script lang="ts" setup>
import { ref, inject, computed, watch } from "vue";
import SelectButton from "primevue/selectbutton";
import { BeakerSession } from "beaker-kernel/src";
import { BeakerRenderOutput } from "../../renderers";

const props = defineProps([
    "mimeBundle",
    "collapse",
]);

const session = inject<BeakerSession>('session');

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
}

.mime-payload {
    overflow-x: auto;
    display: flex;
    flex-direction: column
}
</style>
