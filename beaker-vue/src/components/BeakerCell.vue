<template>
  <div
    class="beaker-cell"
    tabindex="0"
    @keyup.enter.exact="focusEditor"
    @keydown.ctrl.enter.prevent="execute"
    @keydown.shift.enter.prevent="executeAndMove"
    @keyup.esc="unfocusEditor"
    ref="beakerCellRef"
  >
    <div class="cell-grid">
      <div
        class="drag-handle"
        :class="{
            'drag-disabled': !props.dragEnabled,
        }"
      >
        <DraggableMarker
            :draggable="props.dragEnabled"
        />
      </div>

      <div class="cell-contents">
        <!-- pass properties for index and funcs down so that if the given component -->
        <!-- needs further control over how its children render, that it can -->
        <Component
            :is="componentMap[props.cell.cell_type || 'raw']"
            :cell="props.cell"
            ref="typedCellRef"
            
            :index="index"
            :selectedCellIndex="selectedCellIndex"
            :childOnClickCallback="childOnClickCallback"
            :selectNext="() => emit('keyboard-nav', 'select-next-cell')"
        />
        <!-- fallback/standard child rendering, if cell does not take ownership of it -->
        <!-- TODO: best representation of which cells must handle their own subtree rendering -->
        <div class="cell-children" v-if="typeof props.cell?.custom_child_renderer === 'undefined'">
            <Component
                v-for="(child, subindex) in props.cell?.children"
                :key="child.id"
                :is="componentMap[child.cell_type || 'raw']"
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
import { defineProps, ref, computed, defineEmits, defineExpose, Component, inject } from "vue";
import DraggableMarker from './DraggableMarker.vue';
import BeakerCodeCell from './BeakerCodecell.vue';
import BeakerMarkdownCell from './BeakerMarkdownCell.vue';
import BeakerLLMQueryCell from './BeakerLLMQueryCell.vue';
import { BeakerSession } from 'beaker-kernel';

const props = defineProps([
    'index',
    'cell',
    'dragEnabled',
    'selectedCellIndex',
    'childOnClickCallback',
    'getCell'
]);

const emit = defineEmits([
    'move-cell',
    'keyboard-nav'
]);

const session: BeakerSession = inject("session");

type BeakerCellType = typeof BeakerCodeCell | typeof BeakerLLMQueryCell | typeof BeakerMarkdownCell;

const beakerCellRef = ref<HTMLDivElement|null>(null);
const typedCellRef = ref<BeakerCellType|null>(null);
const childrenRef = ref<BeakerCellType|null>(null);

const componentMap: {[key: string]: Component} = {
    'code': BeakerCodeCell,
    'query': BeakerLLMQueryCell,
    'markdown': BeakerMarkdownCell
}

const getSelectedChild = (): number | undefined => {
    return props.selectedCellIndex.split(":").map((part: string) => Number(part))?.[1];
}

function focusEditor() {
    const child = getSelectedChild();
    const targetRef = (typeof(child) !== "undefined") ? childrenRef[child] : beakerCellRef;
    
    if (targetRef.value) {
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
    
    targetRef.value?.execute(session);
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

    grid-template-areas:
        "drag-handle cell-contents";

    grid-template-columns: 1.4rem auto;
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
</style>
