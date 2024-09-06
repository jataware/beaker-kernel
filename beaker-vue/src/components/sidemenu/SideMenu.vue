<template>
    <div class="sidemenu" :class="[position, (minimizeIndicator ? 'minimize' : undefined)]" :style="containerStyle" ref="panelRef">
        <div class="sidemenu-menu-selection" :class="[position]" ref="menuRef">
            <Button
                v-for="(panel, index) in panels" :key="`button-${index}`"
                :class="['menu-button', props.highlight, props.position, (selectedTabIndex === index ? 'selected' : undefined), (props.showLabel ? 'show-label' : undefined)]"
                :icon="panel.props.icon"
                :label="props.showLabel ? panel.props.label : undefined"
                icon-pos="top"
                @click="handleButtonClick(index)"
                v-tooltip:[toolTipArgs]="props.showTooltip ? panel.props.label : undefined"
                text
            ></Button>
        </div>
        <div v-show="expanded" role="menu" class="sidemenu-panel-container">
            <component v-for="(panel, index) in panels" :key="`panel-${index}`" :is="panel" v-show="selectedTabIndex === index" ></component>
        </div>
        <div v-if="expanded && !staticSize"
            class="sidemenu-gutter"
            @mousedown.prevent="startDrag"
            ref="gutterRef"
        >
            <div class="sidemenu-gutter-handle"></div>
        </div>
    </div>
</template>

<script setup lang="tsx">
import { ref, defineProps, defineExpose, computed, defineEmits, useSlots, isVNode, nextTick, withDefaults, onMounted } from "vue";

import Button from 'primevue/button';
import SideMenuPanel from "./SideMenuPanel.vue";

export type MenuPosition = "right" | "left";
export type HighlightType = "full" | "shadow" | "line";

export interface Props {
    style?: any;
    expanded?: boolean,
    position?: MenuPosition;
    highlight?: HighlightType;
    showLabel?: boolean;
    showTooltip?: boolean;
    staticSize?: boolean,
    initialWidth?: string,
    resizable?: boolean,
}

const props = withDefaults(defineProps<Props>(), {
    style: {},
    expanded: true,
    highlight: "full",
    position: "right",
    showLabel: false,
    showTooltip: true,
    staticSize: false,
    initialWidth: '100%',
    resizable: true,
});

const emit = defineEmits([
    "panel-hide",
    "panel-show",
]);

const AUTO_CLOSE_MARGIN = 50;
const MINIMIZE_INDICATION_WIDTH = 4;

const slots = useSlots();

const selectedTabIndex = ref(props.expanded ? 0 : -1);
const panelWidth = ref<number|null>(null);
const listeners = ref({
    move: null,
    end: null,
});
const dragStartPos = ref<number|null>(null);
const dragStartWidth = ref<number|null>(null);
const dragDistance = ref<number|null>(null);
const panelRef = ref(null);
const menuRef = ref(null);
const gutterRef = ref(null);
const minimizeIndicator = ref<boolean>(false);

// const minWidth = () => {
//     return gutterRef.value.clientWidth + menuRef.value.clientWidth + AUTO_CLOSE_MARGIN;

// }

var minWidth: number;
var menuWidth: number;
var closedWidth: number;

const expanded = computed(() => {
    const res = selectedTabIndex.value > -1;
    return res
});

const panels = computed(() => {
    return slots.default().filter((item) => {
        return (isVNode(item) && item.type === SideMenuPanel);
    });
});

const isStatic = computed(() => (props.staticSize || (expanded.value && panelWidth.value === null)))

const containerStyle = computed(() => {
    if (expanded.value) {
        return {
            ...props.style,
            width: (panelWidth.value !== null ? `${panelWidth.value}px` : props.initialWidth)
        };
    }
    else {
        return {
            ...props.style,
        };
    }
});

const toolTipArgs = computed(() => {
    return {position: ({left: "right", right: "left"}[props.position])};
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
    dragStartWidth.value = panelWidth.value || panelRef.value.clientWidth;
    menuWidth = gutterRef.value.clientWidth + menuRef.value.clientWidth;
    closedWidth = menuWidth + MINIMIZE_INDICATION_WIDTH;
    minWidth = menuWidth + AUTO_CLOSE_MARGIN;
};

const moveDrag = (evt: MouseEvent) => {
    let width: number;
    dragDistance.value = evt.x - dragStartPos.value;
    if (props.position === "left") {
        width = dragStartWidth.value + dragDistance.value;
    }
    else {
        width = dragStartWidth.value - dragDistance.value;
    }
    if (width <= minWidth) {
        // Will be minimizing
        if (panelWidth.value != closedWidth) {
            console.log('minimzing');
            panelWidth.value = closedWidth;
            minimizeIndicator.value = true;
        }
    }
    else {
        panelWidth.value = width;
        minimizeIndicator.value = false;
    }

}

const endDrag = (evt: MouseEvent) => {
    document.removeEventListener("mousemove", moveDrag);
    document.removeEventListener("mouseup", endDrag);
    // If dragged closed, assume they want the panel to be hidden
    if (panelWidth.value <= minWidth) {
        selectedTabIndex.value = -1;
        panelWidth.value = null;
    }
    dragStartPos.value = null;
    dragDistance.value = null;
    minimizeIndicator.value = false;

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
    if (minimizeIndicator.value) {
        minimizeIndicator.value = false;
    }
}

defineExpose({
    selectPanel
});

</script>


<style lang="scss">
.sidemenu {
    height: 100%;
    display: grid;
    box-sizing: border-box;
    border: 1px solid var(--surface-border);
    width: 100%;

    &.right {
        grid:
            "handle content menu" 100% /
            max-content minmax(0px, 1fr) max-content;
    }

    &.left {
        grid:
            "menu content handle" 100% /
            max-content minmax(0px, 1fr) max-content;
    }

    &.minimize {
        .sidemenu-gutter {
            width: 8px;
            background-color: var(--primary-color);
        }
    }
}

.sidemenu-panel-container {
    grid-area: content;
    box-sizing: border-box;
    height: 100%;
    width: 100%;
}

.sidemenu-menu-selection {
    grid-area: menu;
    background-color: var(--surface-b);
    display: flex;
    flex-direction: column;
    width: 100%;
    &.right {
        margin-left: 2px;
    }
    &.left {
        margin-right: 2px;
    }
}

.sidemenu-gutter {
    grid-area: handle;
    width: 4px;
    display: flex;
    flex-direction: row;
    align-items: center;

    &:hover {
        cursor: col-resize;
    }
}

.sidemenu-gutter-handle {
    width: 8px;
    z-index: 100;
    height: 3rem;
    background-color: #777;
    display: flex;
    justify-content: space-around;
    align-items: center;
    overflow: clip;
    border: 1px outset #000;

    &:before {
        filter: blur(0.75px);
        color: #333;
        writing-mode: vertical-rl;
        text-orientation: sideways-right;
        letter-spacing: -1px;
        content: "▮▮▮▮▮▮";
        position: relative;
        left: -6px;
        font-size: 20px;
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

</style>
