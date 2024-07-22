<template>
  <div
    class="beaker-cell"
    tabindex="0"
    @click="clicked"
    ref="beakerCellRef"
  >
    <div class="cell-grid">
      <div
        class="drag-handle"
      >
        <DraggableMarker
            :draggable="props.dragEnabled"
        />
      </div>
      <Dropdown
        class="cell-type-selector"
        v-model="cell.cell_type"
        :options="Object.keys(cellMap || {})"
        dropdown-icon="pi pi-code"
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
      <div class="cell-contents">
        <slot name="default">
        </slot>

        <slot name="child-cells">
        </slot>
      </div>
    </div>
  </div>
</template>


<script setup lang="ts">
import { defineProps, ref, inject } from "vue";
import DraggableMarker from './DraggableMarker.vue';
import BeakerCodeCell from './BeakerCodeCell.vue';
import BeakerMarkdownCell from './BeakerMarkdownCell.vue';
import BeakerLLMQueryCell from './BeakerLLMQueryCell.vue';
import { BeakerNotebookComponentType } from '@/components/notebook/BeakerNotebook.vue';

import BeakerRawCell from './BeakerRawCell.vue';
import { IBeakerCell } from "beaker-kernel";
import Dropdown from 'primevue/dropdown';

export type CellTypes =
    | typeof BeakerRawCell
    | typeof BeakerCodeCell
    | typeof BeakerMarkdownCell
    | typeof BeakerLLMQueryCell;

export interface Props {
    cell: IBeakerCell;
    dragEnabled?: boolean;
}

const myRef = ref();

const props = defineProps<Props>();

const cell = ref(props.cell);

const notebook = inject<BeakerNotebookComponentType>("notebook");
const cellMap = inject("cell-component-mapping");

const clicked = (evt) => {
    notebook.selectCell(cell.value as {id: string}, );
};

const beakerCellRef = ref<HTMLDivElement|null>(null);


const cellIconMap = {
    "code": "pi pi-code",
    "markdown": "pi pi-pencil",
    "query": "pi pi-sparkles",
    "raw": "pi pi-question-circle",
};

enum CellState {
  Success = 'success',
  Modified = 'modified',
  Error = 'error',
  Pending = 'pending',
}

const cellState = ref<CellState>(CellState.Pending);
</script>

<style lang="scss">

.beaker-cell {
    padding: 1rem 0 1rem 0.2rem;
    border-right: 5px solid transparent;
    background-color: var(--surface-a);
    border-bottom: 4px solid var(--surface-c);

    &.selected {
      border-right: 5px solid var(--purple-400);
      border-top: unset;
      background-color: var(--surface-ground);
    }

    &:focus {
        outline: none;
    }
}

.cell-grid {
    display: grid;
    justify-content: start;
    grid-template-areas:
        "cell-type-dropdown drag-handle cell-contents";

    grid-template-columns: 2rem 1.4rem 1fr;
}

.cell-contents {
  grid-area: cell-contents;
}

.drag-handle {
  grid-area: drag-handle;
  margin-left: auto;
  margin-right: auto;

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
    background-color: #222;
    > * {
        opacity: 0.5;
        background-color: #222;
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


.cell-type-selector {
    grid-area: cell-type-dropdown;
    margin-left: auto;
    margin-right: auto;
    width: 1.5rem;
    aspect-ratio: 1 / 1;
    padding: 0;
    border-color: #c5c6cc;
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
</style>
