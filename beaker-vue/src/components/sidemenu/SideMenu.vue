<template>
    <div class="sidemenu-container" :class="[position]">
        <div class="sidemenu" :class="[position, (minimizeIndicator ? 'minimize' : undefined)]" :style="containerStyle" ref="panelRef">
            <div class="sidemenu-menu-selection" :class="[position]" ref="menuRef">
                <div
                    v-for="buttonPosition in ['top', 'middle', 'bottom']"
                    :key="buttonPosition"
                    :position="buttonPosition"
                    :class="['button-panel', `${buttonPosition}-buttons`]"
                >
                    <Button
                        v-for="{panel, idx} in panelsByPosition[buttonPosition]" :key="`button-${buttonPosition}-${idx}`"
                        :class="[
                            'menu-button',
                            props.highlight,
                            props.position,
                            (selectedTabIndex === idx ? 'selected' : undefined),
                            (props.showLabel ? 'show-label' : undefined),
                        ]"
                        :icon="panel.props?.icon"
                        :label="props.showLabel ? panel.props.label : undefined"
                        icon-pos="top"
                        @click="handleButtonClick(idx)"
                        v-tooltip:[toolTipArgs]="props.showTooltip ? panel.props.label : undefined"
                        text
                    ></Button>
                </div>
            </div>
            <div v-show="expanded" role="menu" class="sidemenu-panel-container">
                <component
                    v-for="(panel, index) in panels"
                    :key="`panel-${index}`"
                    :is="panel"
                    v-show="selectedTabIndex === index"
                    :selected="selectedTabIndex === index"
                />
            </div>
            <div v-if="expanded && !staticSize"
                class="sidemenu-gutter"
                @mousedown.prevent="startDragHandle"
                ref="gutterRef"
            >
                <div v-if="!staticSize" class="sidemenu-gutter-handle"></div>
            </div>
        </div>
    </div>
</template>

<script setup lang="tsx">
import { ref, defineProps, defineExpose, watch, computed, defineEmits, getCurrentInstance, useSlots, isVNode, nextTick, withDefaults, onUnmounted, onMounted } from "vue";
import { type VNode } from "vue";

import Button from 'primevue/button';
import SideMenuPanel from "./SideMenuPanel.vue";

export type MenuPosition = "right" | "left";
export type HighlightType = "full" | "shadow" | "line";

interface SideMenuProps {
    style?: {[key: string]: string};
    expanded?: boolean,
    position?: MenuPosition;
    highlight?: HighlightType;
    showLabel?: boolean;
    showTooltip?: boolean;
    staticSize?: boolean;
    initialWidth?: string;
    resizable?: boolean;
    maximized?: boolean;
}

const props = withDefaults(defineProps<SideMenuProps>(), {
    style: () => {return {}},
    expanded: true,
    highlight: "full",
    position: "right",
    showLabel: false,
    showTooltip: true,
    staticSize: false,
    initialWidth: '100%',
    resizable: true,
    maximized: false,
});

const emit = defineEmits([
    "panel-hide",
    "panel-show",
    "resize",
]);

const AUTO_CLOSE_MARGIN = 50;
const MINIMIZE_INDICATION_WIDTH = 8;

const slots = useSlots();

const selectedTabIndex = ref<number|null>(props.expanded ? 0 : null);
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
const resizeObserver = ref<ResizeObserver>();
const resizeHistory = ref<DOMRectReadOnly>();
const instance = getCurrentInstance();

var minWidth: number;
var menuWidth: number;
var closedWidth: number;

const expanded = computed(() => {
    return selectedTabIndex.value !== null;
});

const panels = computed(() => {
    const slotPanels = slots.default().filter((item) => {
        return (isVNode(item) && item.type === SideMenuPanel);
    });
    return slotPanels;
})

const panelsByPosition = computed(() => {
    const result: {[key: string]: {panel: VNode; idx: number}[]} = {
        top: [],
        middle: [],
        bottom: [],
    }
    panels.value?.forEach((panel, idx) => {
        const panelPos = panel.props.position || "top";
        result[panelPos].push({panel, idx});
    });
    return result;
});

const isStatic = computed(() => (props.staticSize || (expanded.value && panelWidth.value === null)))

const containerStyle = computed(() => {
    if (expanded.value) {
        var width: string;
        if (panelWidth.value !== null) {
            width = `${panelWidth.value}px`;
        }
        else if (props.maximized) {
            width = props.initialWidth;
        }
        else {
            const currWidth = (instance?.vnode?.el as HTMLDivElement)?.clientWidth;
            if (currWidth) {
                width = `${currWidth}px`;
            }
            else {
                width = props.initialWidth;
            }
        }
        return {
            ...props.style,
            width: width,
        };
    }
    else {
        return {
            ...props.style,
        };
    }
});

watch(expanded, () => {
    nextTick(() => {
        const offsetParent = instance.vnode.el.offsetParent;
        const backoff = offsetParent.scrollWidth - offsetParent.offsetWidth;
        if (backoff > 0) {
            panelWidth.value -= backoff;
        }
    });
});

const toolTipArgs = computed(() => {
    return {position: ({left: "right", right: "left"}[props.position])};
});

const startDragHandle = (evt: MouseEvent) => {
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
    listeners.value.move = document.addEventListener("mousemove", moveDragHandle);
    listeners.value.end = document.addEventListener("mouseup", endDragHandle);

    dragStartPos.value = evt.x;
    dragStartWidth.value = panelWidth.value || panelRef.value.clientWidth;
    menuWidth = menuRef.value.clientWidth;
    closedWidth = menuWidth + MINIMIZE_INDICATION_WIDTH;
    minWidth = menuWidth + AUTO_CLOSE_MARGIN;
};

const moveDragHandle = (evt: MouseEvent) => {
    let width: number;
    let resize = true;
    dragDistance.value = evt.x - dragStartPos.value;
    if (props.position === "left") {
        width = dragStartWidth.value + dragDistance.value;
    }
    else {
        width = dragStartWidth.value - dragDistance.value;
    }
    if (width <= minWidth) {
        resize = false;
        // Will be minimizing
        if (panelWidth.value != closedWidth) {
            resize = true;
            width = closedWidth;
            minimizeIndicator.value = true;
        }
    }
    else {
        minimizeIndicator.value = false;
    }

    if (resize) {
        panelWidth.value = width;
    }

    nextTick(() => {
        const offsetParent = instance.vnode.el.offsetParent;
        const backoff = offsetParent.scrollWidth - offsetParent.offsetWidth;
        if (backoff > 0) {
            panelWidth.value -= backoff;
        }
    });
}

const endDragHandle = (evt: MouseEvent) => {
    document.removeEventListener("mousemove", moveDragHandle);
    document.removeEventListener("mouseup", endDragHandle);
    // Normalize position to closes full pixel. Prevent display errors for partial pixel sizes.
    panelWidth.value = Math.round(panelWidth.value);
    // If dragged closed, assume they want the panel to be hidden
    if (panelWidth.value <= minWidth) {
        selectedTabIndex.value = null;
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
        selectedTabIndex.value = null;
        emit("panel-hide");
    }
}

const isPanelSelected = (index: number) => {
    return Boolean(
        selectedTabIndex.value !== null &&
        selectedTabIndex.value === index
    );
}

const hidePanel = () => {
    selectedTabIndex.value = null;
}

const selectPanel = (id_or_label: string) => {
    selectedTabIndex.value = panels.value.findIndex(
        (panel) => (panel.props?.label === id_or_label || panel.props?.id === id_or_label)
    );
    if (minimizeIndicator.value) {
        minimizeIndicator.value = false;
    }
}

onMounted(() => {
    const target: HTMLElement = document.body;
    // Observer to smoothly resize the side menu when the document size changes (maximizing/resizing a browser window)
    resizeObserver.value = new ResizeObserver((entries) => {
        for (const entry of entries) {
            if (!resizeHistory.value) {
                resizeHistory.value = entry.contentRect;

            }
            else if (entry.contentRect !== resizeHistory.value) {
                if (panelWidth.value) {
                    const resizeRatio = entry.contentRect.width / resizeHistory.value.width;
                    panelWidth.value = panelWidth.value * resizeRatio;
                }
                resizeHistory.value = entry.contentRect;
            }
        }

    });
    resizeObserver.value.observe(target);
})

onUnmounted(() => {
    resizeObserver.value.disconnect();
    resizeObserver.value = null;
})

defineExpose({
    selectPanel,
    hidePanel
});

</script>


<style lang="scss">
.sidemenu-container {
    height: 100%;
    width: 100%;
    display: grid;
    &.right {
        grid:
            "spacer sidemenu" 100% /
            1fr max-content;

    }
    &.left {
        grid:
            "sidemenu spacer" 100% /
            max-content 1fr;
    }
}

.spacer {
    grid-area: spacer;
    flex-grow: 1;
    flex-shrink: 1000;
}

.sidemenu {
    grid-area: sidemenu;
    height: 100%;
    display: grid;
    box-sizing: border-box;
    width: 100%;

    &.right {
        grid:
            "gutter content menu" 100% /
            4px minmax(0px, 1fr) max-content;

        .sidemenu-panel-container {
            margin-left: 6px;
        }
    }

    &.left {
        grid:
            "menu content gutter" 100% /
            max-content minmax(0px, 1fr) 4px;

        .sidemenu-panel-container {
            margin-right: 6px;
        }
    }

    &.minimize {
        .sidemenu-gutter {
            width: 8px;
            background-color: var(--primary-color);
            .sidemenu-gutter-handle {
                right: -4px;
            }

        }
        .sidemenu-panel-container, .side-panel {
            width: 0;
            overflow: hidden;
            margin: 0;
        }
    }
}

.sidemenu-panel-container {
    grid-area: content;
    box-sizing: border-box;
    height: 100%;
    width: 100%;
    overflow: hidden;
}

.sidemenu-menu-selection {
    position: sticky;
    border: 1px solid var(--surface-border);
    grid-area: menu;
    background-color: var(--surface-b);
    display: flex;
    flex-direction: column;
    min-width: 4rem;

    > div {
        display: flex;
        flex-direction: column;

        &.button-panel {
            flex: 1;
        }
        &.bottom-buttons {
            flex-direction: column;
            justify-content: end;
        }
    }
}

.sidemenu-gutter {
    grid-area: gutter;
    position: relative;
    display: grid;
    flex-direction: row;
    align-items: center;
    background-color: var(--surface-border);
    z-index: 40;

    &:hover {
        cursor: col-resize;
    }
}

.sidemenu-gutter-handle {
    display: flex;
    position: absolute;
    right: -6px;
    width: 14px;
    z-index: 100;
    height: 3rem;
    background-color: var(--surface-400);
    justify-content: space-around;
    align-items: center;
    overflow: clip;
    border: 1px outset var(--surface-500);

    &:before {
        filter: blur(0.75px);
        color: var(--surface-50);
        writing-mode: sideways-lr;
        letter-spacing: -1px;
        content: "▮▮▮▮▮▮";
        position: relative;
        left: -6px;
        font-size: 20px;
    }
}

button.menu-button {
    background-color: transparent;
    color: var(--primary-300);
    border-color: transparent;
    aspect-ratio: 1;
    width: 100%;
    padding: .75rem .5rem;

    // Increase size of icon if no text
    &.p-button-icon-only .p-button-icon{
        font-size: 1.75rem;
    }

    &:focus {
        box-shadow: none;
    }

    &:hover {
        color: var(--primary-700);
        background-color: var(--surface-c);
        border-color: var(--primary-700);
    }

    &.disabled {
        color: var(--surface-200);
        cursor: default;
        &:hover {
            background-color: var(--surface-c);
            border-color: var(--surface-200);

        }
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
