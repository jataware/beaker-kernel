<template>
    <div class="sidemenu-container" :class="[position]">
        <div v-show="expanded"
            class="sidemenu-gutter"
            @mousedown.prevent="startDrag"
        >
            <div class="sidemenu-gutter-handle"></div>
        </div>
        <div v-show="expanded" role="menu" class="sidemenu-panel-container" :style="{width: `${panelWidth}px`}">
            <component v-for="(panel, index) in panels" :key="`panel-${index}`" :is="panel" v-show="selectedTabIndex === index" ></component>
        </div>
        <div class="sidemenu-menu-selection" :class="[position]">
            <Button
                v-for="(panel, index) in panels" :key="`button-${index}`"
                :class="['menu-button', props.highlight, props.position, (selectedTabIndex === index ? 'selected' : undefined), (props.showLabel ? 'show-label' : undefined)]"
                :icon="panel.props.icon"
                :label="props.showLabel ? panel.props.label : undefined"
                icon-pos="top"
                v-tooltip.left="props.showTooltip ? panel.props.label : undefined"
                @click="handleButtonClick(index)"
            ></Button>
        </div>
    </div>
</template>

<script setup lang="tsx">
import { ref, defineProps, defineExpose, computed, defineEmits, useSlots, isVNode, nextTick, withDefaults } from "vue";

import Button from 'primevue/button';
import SideMenuPanel from "@/components/sidemenu/SideMenuPanel.vue";

export type MenuPosition = "right" | "left";
export type HighlightType = "full" | "shadow" | "line";

export interface Props {
    position?: MenuPosition;
    highlight?: HighlightType;
    showLabel?: boolean;
    showTooltip?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
    highlight: "full",
    position: "right",
    showLabel: false,
    showTooltip: true,
});

const emit = defineEmits([
    "panel-hide",
    "panel-show",
]);

const DEFAULT_PANELWIDTH = 400;

const slots = useSlots();

const selectedTabIndex = ref(0);
const panelWidth = ref(DEFAULT_PANELWIDTH);
const listeners = ref({
    move: null,
    end: null,
});
const dragStartPos = ref<number|null>(null);
const dragStartWidth = ref<number|null>(null);
const dragDistance = ref<number|null>(null);

const activePanel = computed(() => {
    return panels.value[selectedTabIndex.value];
});

const expanded = computed(() => {
    return selectedTabIndex.value > -1;
});

const panels = computed(() => {
    return slots.default().filter((item) => {
        return (isVNode(item) && item.type === SideMenuPanel);
    });
});

const startDrag = (evt: MouseEvent) => {
    if (listeners.value.move !== null) {
        try {
            document.removeEventListener("mousemove", listeners.value.move);
        }
        catch (e) {null}
        listeners.value.move = null;
    }
    if (listeners.value.end !== null) {
        try {
            document.removeEventListener("mouseup", listeners.value.end);
        }
        catch (e) {null}
        listeners.value.end = null;
    }
    listeners.value.move = document.addEventListener("mousemove", moveDrag);
    listeners.value.end = document.addEventListener("mouseup", endDrag);

    dragStartPos.value = evt.x;
    dragStartWidth.value = panelWidth.value;
};

const moveDrag = (evt: MouseEvent) => {
    dragDistance.value = evt.x - dragStartPos.value;
    if (props.position === "left") {
        panelWidth.value = dragStartWidth.value + dragDistance.value;
    }
    else {
        panelWidth.value = dragStartWidth.value - dragDistance.value;
    }
}

const endDrag = (evt: MouseEvent) => {
    document.removeEventListener("mousemove", moveDrag);
    document.removeEventListener("mouseup", endDrag);
    // If dragged closed, assume they want the panel to be hidden
    if (panelWidth.value <= 10) {
        selectedTabIndex.value = -1;
        panelWidth.value = DEFAULT_PANELWIDTH;
    }
    dragStartPos.value = null;
    dragDistance.value = null;

};

const handleButtonClick = (index: number) => {
    if (selectedTabIndex.value !== index) {
        selectedTabIndex.value = index;
        emit("panel-show");
    }
    else {
        selectedTabIndex.value = -1;
        emit("panel-hide");
    }
}

const selectPanel = (id: string) => {
    selectedTabIndex.value = panels.value.findIndex((panel) => (panel.props?.tabId === id));
}

defineExpose({
    selectPanel
});

</script>


<style lang="scss">
.sidemenu-container {
    display: flex;
    flex: 1;
    &.right {
        flex-direction: row;
    }
    &.left {
        flex-direction: row-reverse;
    }
}

button.menu-button {
    background-color: transparent;
    color: var(--primary-800);
    border-color: transparent;

    &.show-label {
        padding: .75rem .5rem;
    }

    .p-button-label {
        font-size: smaller;
    }

    &:focus {
        box-shadow: none;
    }

    &:hover {
        color: var(--primary-700);
        background-color: var(--surface-c);
        border-color: var(--primary-700);
    }
    &.line {
        border-radius: 0;
    }
    &.line.right {
        border-width: 0 5px 0 0;
    }
    &.line.left {
        border-width: 0 0 0 5px;
    }
    &.full.selected {
        background-color: var(--primary-color);
        color: var(--surface-b);
    }

    &.selected {
        border-color: var(--primary-color);
        color: var(--primary-color);
    }

    &.shadow:hover {
        box-shadow: inset 0 0 15px var(--primary-800);
    }
    &.shadow.selected {
        box-shadow: inset 0 0 15px var(--primary-color);
    }
}

.sidemenu-panel-container {
    position: relative;
    flex: 1;
}

.sidemenu-menu-selection {
    background-color: var(--surface-b);
    display: flex;
    flex-direction: column;
    &.right {
        margin-left: 2px;
    }
    &.left {
        margin-right: 2px;
    }
}

.sidemenu-gutter {
    width: 4px;
    align-items: center;
    flex-direction: row;
    display: flex;

    &:hover {
        cursor: col-resize;
    }
}

.sidemenu-gutter-handle {
    width: inherit;
    height: 3rem;
    background-color: grey;
}
</style>
