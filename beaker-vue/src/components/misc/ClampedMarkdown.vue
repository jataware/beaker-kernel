<template>
    <div class="clamped-markdown">
        <div
            ref="contentEl"
            class="skill-description clamped-markdown-content"
            :class="{ clamped: !expanded, faded: !expanded && overflowing }"
            v-html="html"
            @click="(event) => emit('link-click', event)"
        ></div>
        <Button
            v-if="overflowing"
            class="clamped-markdown-toggle"
            :label="expanded ? 'Show less' : 'Show more'"
            :icon="expanded ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"
            severity="secondary"
            text
            size="small"
            @click="expanded = !expanded"
        />
    </div>
</template>


<script setup lang="ts">
// Rendered markdown clamped to a preview height, with a Show more/Show less
// toggle that only appears when the content actually overflows the clamp.

import { ref, watch, nextTick } from 'vue';
import Button from 'primevue/button';

const props = defineProps<{ html: string }>();

const emit = defineEmits<{
    (e: 'link-click', event: MouseEvent): void,
}>();

const contentEl = ref<HTMLElement>();
const expanded = ref<boolean>(false);
const overflowing = ref<boolean>(false);

watch(() => props.html, async () => {
    expanded.value = false;
    await nextTick();
    const el = contentEl.value;
    overflowing.value = !!el && el.scrollHeight > el.clientHeight + 1;
}, { immediate: true });

</script>


<style lang="scss">
.clamped-markdown {
    display: flex;
    flex-direction: column;
    min-width: 0;
    max-width: 100%;
}

.clamped-markdown-content {
    &.clamped {
        max-height: 18rem;
        overflow: hidden;
    }

    &.faded {
        mask-image: linear-gradient(to bottom, black 65%, transparent 100%);
        -webkit-mask-image: linear-gradient(to bottom, black 65%, transparent 100%);
    }
}

.clamped-markdown-toggle {
    align-self: center;
}
</style>
