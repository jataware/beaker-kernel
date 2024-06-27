<template>
  <div
    class="beaker-cell"
    tabindex="0"
    @keyup.enter.exact="focusEditor"
    @keydown.ctrl.enter.prevent="execute"
    @keydown.shift.enter.prevent="executeAndMove"
    @keyup.esc="unfocusEditor"
    @cell-state-changed="cellStateChanged"
    @keydown.y="(event) => switchCellTypeContextualEvent(event, 'code')"
    @keydown.m="(event) => switchCellTypeContextualEvent(event, 'markdown')"
    @keydown.r="(event) => switchCellTypeContextualEvent(event, 'raw')"
    ref="beakerCellRef"
  >
    <div class="cell-grid">

      <div class="cell-contents">
        <!-- pass properties for index and funcs down so that if the given component -->
        <!-- needs further control over how its children render, that it can -->
        <Component
            :is="cellComponent"
            :cell="props.cell"
            ref="typedCellRef"
            :index="index"
            :selectedCellIndex="selectedCellIndex"
            :childOnClickCallback="childOnClickCallback"
            :selectNext="() => emit('keyboard-nav', 'select-next-cell')"
        />
        <!-- fallback/standard child rendering, if cell does not take ownership of it -->
        <!-- TODO: best representation of which cells must handle their own subtree rendering -->
        <div class="cell-children" v-if="!customChildRendererMap[props.cell.cell_type || 'raw']">
            <Component
                v-for="(child, subindex) in props.cell?.children"
                :key="child.id"
                :is="cellComponent"
                :cell="child"
                :index="`${index}:${subindex}`"
                :class="{
                    selected: (index === selectedCellIndex)
                }"
                ref="childrenRef"
                drag-enabled=false
                @click.stop="childOnClickCallback(`${index}:${subindex}`)"
                @keyup.esc="unfocusEditor"
            />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, ref, computed, defineEmits, defineExpose, withDefaults, inject  } from "vue";
import DraggableMarker from './DraggableMarker.vue';
import BeakerCodeCell from './BeakerCodecell.vue';
import BeakerMarkdownCell from './BeakerMarkdownCell.vue';
import BeakerLLMQueryCell from './BeakerLLMQueryCell.vue';
import { BeakerSession } from 'beaker-kernel';

import BeakerRawCell from './BeakerRawCell.vue';
import { IBeakerCell } from "beaker-kernel/dist/notebook";
import Dropdown from 'primevue/dropdown';

export type CellTypes = 
    | typeof BeakerRawCell 
    | typeof BeakerCodeCell 
    | typeof BeakerMarkdownCell 
    | typeof BeakerLLMQueryCell;

export interface Props {
    cell: IBeakerCell;
    index: string;
    availableCellTypes: {[key: string]: CellTypes};
    dragEnabled?: boolean;
    childOnClickCallback: CallableFunction;
    getCell: CallableFunction;
    selectedCellIndex: string;
}
// TODO: Figure out how to properly extend a base component
export interface IBeakerCellComponent {
    focus: () => null;
    execute: () => null;
}
const props = withDefaults(defineProps<Props>(), {
    availableCellTypes: () => {return {
        'code': BeakerCodeCell,
        'markdown': BeakerMarkdownCell,
        'query': BeakerLLMQueryCell,
        'raw': BeakerRawCell,
    }}
});

const emit = defineEmits([
    'move-cell',
    'keyboard-nav'
]);

const session: BeakerSession = inject("session");

type BeakerCellType = typeof BeakerCodeCell | typeof BeakerLLMQueryCell | typeof BeakerMarkdownCell;

const beakerCellRef = ref<HTMLDivElement|null>(null);
const typedCellRef = ref<BeakerCellType|null>(null);
const childrenRef = ref<BeakerCellType|null>(null);

const isOuterCellFocused = () => document.activeElement.classList.contains("beaker-cell");
const switchCellTypeContextualEvent = (event, type) => {
    if (isOuterCellFocused()) {
        cell_type.value = type;
        event.preventDefault();
        event.stopPropagation();
    }
}

// const cellIconMap = {
//     "code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAoCAYAAACM/rhtAAAACXBIWXMAAAsTAAALEwEAmpwYAAABuElEQVR4nO1WXUsCQRTd32ZQvbQmZpSt9kGKsZZp5UeWZMn6VYEsWC8+KJRZ6W5q9RxhEUVERfhvTuw+SJGrFbsqNRfuy517hzNzz7kzFEXsv5hQq6OXnCIAa+QG64SDwk9FoqOZnnCBAKTJDTKEg7puisQw7QAvZrqn4v6RSfQNWxTX19Pb4LL8p9iAcaozAIcmbMheFeAMh5qu9+ktKDyIMLOLjZh9NYDcdQE0Y9MWoHFmDkf3AkJ7O4o5VvcSDm+LX+LeXQ7HDyJMNqc2AC0LHpSeK/DEtlrmJfN7CKRiTddckQ0IL1X5EKoCdKwFIb6eY9bvb81N4yTKbxfQW+2KOTMrXnkvdmNdHYC+3SiKT2WMOebbtsYZDmH/Mtc2b5x1ofhUwXIy0lmA+5c5RfF8dJONxcnjGYJ8onMtpi12ub3SCGrP5Src0U2NRBJvLpJAKo7EYbrlHo2D+nzqiuQ7Y+bg5hRWt0ex1rvDybyT+NfxQW1mF+XhLA3pZjXSoM7flWCYcnTnqeOyvPy8KdboGQyOTnfvs8CLGfmD8Nt6zQHqVHYCUEdukCYcxN8UidBDThH7L/YO0lkO65xU5hsAAAAASUVORK5CYII=",
//     "markdown": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAACXBIWXMAAAsTAAALEwEAmpwYAAABc0lEQVR4nO2YMUoDQRSGP7QSSSWkil3EIoVYpPEOVl5AQfvcxCMoCIIh2HgGG/sUCl5AENxFsVFGBt7KMsxudtddMhPfBz8E8pa8LzPzFgYURVEURVk9toEZkAImkqTALbCbl3gNoLGmsb0PkJUwkWdKZNvJFCQhgCbaCstuQEX4ryviclnhGVvjUqkZh05FNoF5Sf0j0ItBxDICPjy1n8AefoIUsZx5ak8pJlgRy1Wu7oZyghMZ5T7bs/Ak6RXUBCsylwOfsS9xh0HwIga4pphsPEchYoBjz3cnNZqaUJ9JFyLuqHVH8iKRb+CohsQh8NWFSP7l53tJLhLJ/oyDChJj4L2rrZXlQtJ0v78AwxKJodR0dkbafO4Z6Hue2ZJVN7GI2Dw4Y30DuK/ze6GI2NwB68Bag7uEoEQMcC4xbYvEEpbdgIqwqiuSBtDEX/OGXASbyDNDbrNjv8TeyWb8QC6CkwAaMxWTyEr8SiiKoigKDfkBUM4f7jMK7QsAAAAASUVORK5CYII=",
//     "query": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAACXBIWXMAAAsTAAALEwEAmpwYAAAEn0lEQVR4nO2ZeajVRRTHP+/p81m2WlGWWbT4hy1UFC1EhUVJZIRplkuYlrlUmgUVPcIKpD+MSoosabGNhy1GhEHbH0aFhImKoJJmK7Zo3bLnknrjwBk4DHfmN/O7L98V7hcG3p3fzPzmM7+Zc86cB0011VRTJXUyMB14DlgEvATMBi4BWtkPdCbwEVCNlE3AjTSoWoEHgJ0FELa8CfShwfRkBoAtL3vjHANcB5zaExBTSgD8C8wDDtcx5MvcC1RMm7XA/UC/fQXydCbEJ8Dppv8wnXSo/XfapmFAfgBu9izbosS+u4FJPQ3Spab3AG1/EDAH2JH5JfcCV3fnxE8CpgKXJYCIZTpB27UAY4AfSxqGKrAZOKpegBOB14A9Ouj0CMhqYKjpezbwWR0AVVMeqQfiUmCLN2AIZAHQW58dCczXPV5rUuuBEcDlwBeJIL8AvcpAnB9wdCGQ4Vo/FtgamMw2daDt5j2y9UYD3ybAnJYLcQiwMTBYCEQcmuidQL9OYKCJCCYCHcCBWtcXuA/4MwIiwFnqiAwWApGtInrLqxdfcZUZ+xzgc/NcjMBks22OAJ5S5+m/+6YciD5qJXJBbtD6Tv0tKzvDnBvRLGM0/PKVRslOQ4AlXptrc0AuKNinIRC3WmLhXgSO1t+9dau6v6fowQ2N/zZwipnPlWoN5dmAHJC7S4LIIXdbw0lWeCXwm/ZzX0fAHgO2B96xE3jcxGSy7UaRqTklQWwYIiv3inpl22adN6HjA+2qWraoAbBWLllzS4LcovXixf8qGOM9750XAl9G2q/NPR+iu0qC3Kr1Cwr6u5UWteldRNSiN8hNBRH0WakgQxNBHvXqb9f6+QkgYtFEhwJ/Aw+a4LKvno9q5PwkxV1tBeb3IbOCI4ENWj9N659JAJHJu4jY1X2v2xI95LH+M1O/ysyAQ6qqpZltbnDtessbr7/nJYBIiI9+BVtfMVYt1v9dMlTLIVU9jzyhRprniQQQ2R7O+ZYBWUcJiUNaFRl0ubmjiAYD70farzcXpV4lQX4qA+JeOLng7Cz2siBXqDMsinzLgGzIBXgYuFMNgOhgdZhdgRfs0q3V3yzAbZr+sZHvJIXAi70qiSAf5IKsCTikQcAbBR55hlkAp/OAZdrGPdtVAqQjF8S+RMqnen11OhdYWuNFf2ho4TKK/TU0tzdGt8V2ZILs1kxMsloDA8lWeAE4Vtu1aAi/Ub+QH/neEbgxOvP9TyZIJyX0e2TAbeoc3Q2v3UvAucg31F/OG15cVikA2WxCmix9XLBXbQLO+RP5Uq9Hzs8aTTo4Y9CVCFLxLl5ZmpYAYv3Jsxp+VAMTuccccsm0vJpofr8BzqAO9auRDsote3XCA8xXmBoYt+KBrNYgtVv+DTGuDogVwMVmrIuAryPtK8ZIOGPSrXo+E2CrrqTLjMgBXRg5Nz7I/6aWxKh2j16s3H2hTXMAsVzVPgVxuiZyg1uuV1abbo0Fmz0Kgh68EZpxl0j2Z42dnPkdaHJbuaWDBtIgNZe5EHNpQB0HfJgI8CtwPQ2ukQpU698LK/VKbRN6Da/DNI0zTI1AVuqzKfYz/Qcr2bcbKUiQRgAAAABJRU5ErkJggg==",
//     "raw": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAAsTAAALEwEAmpwYAAAB10lEQVR4nO2VSytFURTHf3mMpCiPIgPvARMT+QKU5AMoc2MheU0MxMTASJkwRpkoUW5hzAdQDJRMGHsv7axbq9NFt87Z5x7tf+1a+7/XWWf/9trnXggKCvpLktBYJeMA3iAk6xCSdQiJjLjrSdIQvgAkKQifAJIEhG8AiRsiDQCJEyItAIkLIk0AieF9AaBYSal3IPH3SYmNopX2hiUA8M+ukFUTMAu8FMjbMHnrxm9U7wH4AKqBGuATuNe1Rl8Aec0WyBs168PGH1TvDLg2OTdATuNBHwAuPjedsDmverIVQBlQZbo0pc9sAbum3j6wqfGULwB3ik71kZy8PwD0aZzTtW2dTwMLpt4SMKnxju8rNBPJcZtxmjcnvqBrlzp3V2wEaADqzNzpyieA2+BbJMedvNMJcKhxv64969XqApr1+xgCWoAOoFJzEgfo/KHdT0B5gTrOe9ScHpOzCMxpXAb0+voZdRtHT812YO+XWnuaM2a8g8gz474A3oFuA5Nfn1BvyXjL6k3ofMXUuQNuzXzNF4CYLnQqkPPa1Ts1z1yo16bzI6BWuyf6J9aq3nHSAGmPopX2hiUAkPErFFXsBf+QBICIQgdK7QpJ1j9iCQCEDgQFBfGtL/wpbKROSAb6AAAAAElFTkSuQmCC",
// }

const cellIconMap = {
    "code": "pi pi-code",
    "markdown": "pi pi-pencil",
    "query": "pi pi-sparkles",
    "raw": "pi pi-question-circle",
};

const customChildRendererMap: {[key: string]: boolean} = {
    'query': true,
};

const getSelectedChild = (): number | undefined => {
    return props.selectedCellIndex.split(":").map((part: string) => Number(part))?.[1];
}

enum CellState {
  Success = 'success',
  Modified = 'modified',
  Error = 'error',
  Pending = 'pending',
}

const cell_type = ref<string>((() => props.cell.cell_type || 'raw')());
const cellState = ref<CellState>(CellState.Pending);
const cellComponent = computed((): CellTypes => {
    const component = props.availableCellTypes[cell_type.value];
    if (component) {
        return component;
    }
    else {
        return BeakerRawCell;
    }
});

const cellStateChanged = (newState: CellState) => {
    cellState.value = newState;
};


function focusEditor() {
    const child = getSelectedChild();
    const targetRef = (typeof(child) !== "undefined") ? childrenRef[child] : beakerCellRef;
    if (cell_type.value === "markdown") {
        console.log(typedCellRef.value)
        typedCellRef.value.enter();
    }
    if (targetRef?.value) {
        const editor: HTMLElement|null = targetRef.value.querySelector('.cm-content');
        if (editor) {
            editor.focus();
        }
    }
}

const unfocusEditor = () => {
    if (beakerCellRef.value?.focus) {
        beakerCellRef.value.focus();
    }
};

function execute() {
    const child = getSelectedChild();
    const targetRef = (typeof(child) !== "undefined") ? childrenRef[child] : typedCellRef;
    
    if (targetRef?.value) {
        targetRef.value?.execute(session);
    }

    else {
        props.getCell(props.selectedCellIndex).execute(session);
    }

    unfocusEditor();
    return true;
}

const executeAndMove = () => {
    if (execute()) {
        emit('keyboard-nav', 'select-next-cell');
    }
};

const enter = (event) => {
    const child = getSelectedChild();
    const targetRef = (typeof(child) !== "undefined") ? childrenRef[child] : typedCellRef;
    
    if (targetRef?.value?.enter) {
        targetRef.value.enter(event);
    }
};

defineExpose({
    execute,
    enter,
});

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
