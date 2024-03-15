<template>
  <div
    class="beaker-cell"
    tabindex="0"
    @keyup.enter.exact="focusEditor"
    @keydown.ctrl.enter.prevent="execute"
    @keydown.shift.enter.prevent="executeAndMove"
    @keyup.esc="unfocusEditor"
    @click="handleClick"
    ref="beakerCellRef"
  >
    <div class="cell-grid">
      <div
        class="drag-handle"
        :class="{
            'drag-disabled': !props.dragEnabled,
        }"
      >
        <slot name="drag-indicator">
            <DraggableMarker
                :draggable="props.dragEnabled"
            />
        </slot>
      </div>

      <div class="cell-contents">
        <Component
            :is="componentMap[props.cell.cell_type || 'raw']"
            :cell="props.cell"
            :renderOutput="renderOutput"
            ref="typedCellRef"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, ref, defineEmits, Component, defineExpose } from "vue";
import DraggableMarker from './UIDraggableMarker.vue';
import CodeCell from './UICodeCell.vue';
import MarkdownCell from './UIMarkdownCell.vue';
import AgentCell from './UIAgentCell.vue';

const props = defineProps({
    cell: {
        type: Object,
        required: true
    },
    dragEnabled: {
        type: Boolean,
        default: false
    },
    renderOutput: {
        type: Boolean,
        default: true
    }
});

const emit = defineEmits([
    'keyboard-nav',
    'click'
]);

type BeakerCellType = typeof CodeCell | typeof AgentCell | typeof MarkdownCell;

const beakerCellRef = ref<HTMLDivElement|null>(null);
const typedCellRef = ref<BeakerCellType|null>(null);

const componentMap: {[key: string]: Component} = {
    'code': CodeCell,
    'query': AgentCell,
    'markdown': MarkdownCell
}

function handleClick() {
    emit('click');
}

// Both for code and markdown cells
function focusEditor() {
    if (beakerCellRef.value) {
        const editor: HTMLElement|null = beakerCellRef.value.querySelector('.cm-content');
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
    if (typedCellRef?.value?.execute) {
        typedCellRef.value.execute();
        // For code/markdown cells
        unfocusEditor();
        return true;
    }
    return false;
}

const executeAndMove = () => {
    if (execute()) {
        emit('keyboard-nav', 'select-next-cell');
    }
};

defineExpose({execute});

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
.drag-below {
    box-shadow: 0px 5px 0px var(--purple-200);
    margin-bottom: 5px;
    padding-bottom: calc(1rem - 5px);
}

.drag-itself, .drag-itself.selected {
    background-color: var(--purple-200);
}

</style>
