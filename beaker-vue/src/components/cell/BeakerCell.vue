<template>
    <div
        class="beaker-cell"
        tabindex="0"
        @click="clicked"
        ref="beakerCellRef"
        :class="{collapsed}"
    >
        <div class="collapse-box" @click.capture.stop.prevent="collapseCell"></div>
        <div
            class="drag-handle"
        >
            <DraggableMarker
                :draggable="props.dragEnabled"
            />
        </div>
        <div class="cell-contents">
            <slot name="default">
            </slot>

            <slot name="child-cells">
            </slot>
        </div>

        <div class="menu-area" ref="menuAreaRef">
        <slot name="hover-menu">
            <div class="hover-menu">
                <Button
                    text
                    small
                    icon="pi pi-ellipsis-v"
                    @click="hoverMenuRef.toggle($event)"
                />
                <OverlayPanel
                    class="menu-overlay"
                    ref="hoverMenuRef"
                    :popup="true"
                >
                    <Dropdown
                        class="cell-type-selector"
                        :model-value="cell.cell_type"
                        @update:model-value="(value) => notebook.convertCellType(cell, value)"
                        :options="Object.keys(cellMap || {})"
                        :dropdown-icon="cellIcon"
                    >
                        <template #value="slotProps">
                            <span :class="cellIconMap[slotProps.value]"></span>
                        </template>

                        <template #option="slotProps">
                            <div class="cell-type-dropdown-item">
                                <span :class="cellIconMap[slotProps.option]"></span>
                                <span>{{ slotProps.option }}</span>
                            </div>
                        </template>
                    </Dropdown>
                </OverlayPanel>
            </div>
        </slot>
        </div>
        <div class="extra-area">
            <slot name="extra">
            </slot>
        </div>

    </div>
</template>


<script setup lang="ts">
import { defineProps, ref, inject, computed } from "vue";
import Button from 'primevue/button';
import DraggableMarker from './DraggableMarker.vue';
import BeakerCodeCell from './BeakerCodeCell.vue';
import BeakerMarkdownCell from './BeakerMarkdownCell.vue';
import BeakerLLMQueryCell from './BeakerLLMQueryCell.vue';
import { type BeakerNotebookComponentType } from '../notebook/BeakerNotebook.vue';

import BeakerRawCell from './BeakerRawCell.vue';
import { BeakerBaseCell, type IBeakerCell } from "beaker-kernel";
import Dropdown from 'primevue/dropdown';
import OverlayPanel from 'primevue/overlaypanel';

export type CellTypes =
    | typeof BeakerRawCell
    | typeof BeakerCodeCell
    | typeof BeakerMarkdownCell
    | typeof BeakerLLMQueryCell;

export interface Props {
    cell: IBeakerCell;
    dragEnabled?: boolean;
}

const props = defineProps<Props>();

const notebook = inject<BeakerNotebookComponentType>("notebook");
const cellMap = inject("cell-component-mapping");

const clicked = (evt) => {
    notebook.selectCell(props.cell as {id: string}, );
};

const beakerCellRef = ref<HTMLDivElement|null>(null);
const hoverMenuRef = ref(null);
const collapsed = ref<boolean>(false);

const cellIconMap = {
    "code": "pi pi-code",
    "markdown": "pi pi-pencil",
    "query": "pi pi-sparkles",
    "raw": "pi pi-question-circle",
};

const cellIcon = computed(() => cellIconMap[props.cell.cell_type]);

enum CellState {
    Success = 'success',
    Modified = 'modified',
    Error = 'error',
    Pending = 'pending',
}

const cellState = ref<CellState>(CellState.Pending);

const collapseCell = (evt) => {
    console.log("Shrinking!")
    collapsed.value = !collapsed.value;
};

</script>

<style lang="scss">

.beaker-cell {
    display: grid;
    border-radius: 0;
    position: relative;
    // padding: 0.25em 0.25em 0.25em 0;
    background-color: var(--surface-a);

    // border-left: 4px solid transparent;
    grid:
        "collapse-box drag-handle cell-contents hover-menu" 2em
        "collapse-box drag-handle cell-contents extra" 1fr /
        10px 1.6rem 1fr 2em;

    &.selected .collapse-box {
        background-color: var(--primary-400);
    }

    &:focus {
        outline: none;
    }

    // Separators between cells
    &:not(.collapsed):after {
        content: "";
        position: absolute;
        height: 4px;
        left: 0;
        bottom: -4px;
        right: 0px;
        z-index: 0;
        background-color: var(--surface-border);
    }

    &.collapsed {
        max-height: 3em;
        // border-bottom: 5px dotted black;
    }

    &.collapsed .collapse-box {
        --wave-color: var(--surface-border);
        background-color: var(--wave-color);

        &:after {
            content: "";
            position: absolute;
            z-index: 200;
            height: 10px;
            bottom: -6px;
            left: 0;
            right: 0;
            background-color: var(--wave-color);
            --mask:
                radial-gradient(8.059999999999999px at 50% calc(100% + 4.25px),#0000 calc(99% - 3px),#000 calc(101% - 3px) 99%,#0000 101%) calc(50% - 10px) calc(50% - 4px + .5px)/20px 8px repeat-x,
                radial-gradient(8.059999999999999px at 50% -4.25px,#0000 calc(99% - 3px),#000 calc(101% - 3px) 99%,#0000 101%) 50% calc(50% + 4px)/20px 8px repeat-x;
            -webkit-mask: var(--mask);
            mask: var(--mask);
        }
    }

}

.collapse-box {
    grid-area: collapse-box;
    border: 1px inset var(--surface-border);
    border-top: unset;
    border-bottom: unset;
    cursor: pointer;
}

.cell-contents {
  grid-area: cell-contents;
  margin: 0.25em 0;
}

.drag-handle {
    grid-area: drag-handle;
    align-content: center;
    justify-self: center;
    z-index: 10;

    .draggable-wrapper {
        height: 3rem;
        width: 1rem;
        background-position: 0.5rem 0.5rem;
        background-size: 0.5rem 0.5rem;

        &:hover {
            opacity: 0.9;
        }
    }
}

.drag-disabled {
    pointer-events: none;
    opacity: 0.2;
}

.drag-source {
    &:after {
        content: "";
        position: absolute;
        top: 0px;
        left: 0px;
        bottom: 0px;
        right: 0px;
        z-index: 0;
        background-color: rgba(128, 128, 128, 0.33);
    }
}

.drag-above {
    box-shadow: 0px -5px 1px var(--purple-200);

    &:first-child {
        margin-top: 5px;
        padding-top: calc(1rem - 5px);
    }
}

.drag-itself, .drag-itself.selected {
    background-color: var(--purple-200);
}

.drag-below {
    box-shadow: 0px 5px 0px var(--purple-200);
    margin-bottom: 5px;
    padding-bottom: calc(1rem - 5px);
}

.menu-area {
    grid-area: hover-menu;
    margin: 0.25em 0.25em 0.25em 0;
    height: 100%;
    width: 100%;
    button {
        height: 1.5rem;
        width: unset;
        padding: unset;
        aspect-ratio: 1 / 1;
        font-size: smaller;
    }
}

.menu-overlay .p-overlaypanel-content{
    padding: 0.2rem 3rem;
}

.cell-type-selector {
    grid-area: cell-type-dropdown;
    margin-left: auto;
    margin-right: auto;
    width: 1.5rem;
    aspect-ratio: 1 / 1;
    padding: 0;
    border-color: var(--surface-border);
    display: flex;
    align-items: center;
    justify-content: center;

    .p-dropdown-label {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: auto;
        padding: 0;
        width: 100%;
        aspect-ratio: 1 / 1;
    }
    .p-dropdown-trigger {
        display: none;
        width: 0;
    }
}
.cell-type-dropdown-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    img {
        width: calc(2.5rem - 2px);
        aspect-ratio: 1 / 1;
    }
}

.extra-area {
    margin: 0.25em 0.25em 0.25em 0;
}
</style>
