<template>
    <div class="beaker-notebook">
        <slot></slot>
    </div>
</template>

<script lang="tsx">
import { ref, onBeforeMount, onMounted, defineProps, computed, nextTick, provide, inject, defineEmits, defineExpose } from "vue";
import { ComponentPublicInstance } from '@vue/runtime-core';
import { IBeakerCell, BeakerBaseCell, BeakerSession, BeakerNotebook } from 'beaker-kernel';

import BeakerCell from '@/components/cell/BeakerCell.vue';
import {default as BeakerSessionComponent, IBeakerSession} from "../session/BeakerSession.vue";

export interface IBeakerNotebook extends ComponentPublicInstance {
  beakerSession: IBeakerSession
  session: BeakerSession,
  notebook: BeakerNotebook,
  selectedCellId: string,
  cellCount: number,

  selectedCell: IBeakerCell,
  isEditing: boolean,

  selectCell: (cell: string | {id: string}) => any,
  selectNextCell: (referenceCell?: IBeakerCell) => IBeakerCell | null,
  selectPrevCell: (referenceCell?: IBeakerCell) => IBeakerCell | null,
  insertCellBefore: (referenceCell?: IBeakerCell, cellType?: string) => IBeakerCell,
  insertCellAfter: (referenceCell?: IBeakerCell, cellType?: string) => IBeakerCell,
  removeCell: (cell: IBeakerCell) => IBeakerCell,

}

export default {
    props: [
        "cellMap",
    ],
    emits: [
    ],

    setup(props, { emit }) {

        const session: BeakerSession = inject('session');
        const beakerSession: typeof BeakerSessionComponent = inject('beakerSession');
        const notebook = ref<BeakerNotebook>(session.notebook);

        // TODO: Clear up session/beakerSession confusion. sessionContext? sessionController?
        const selectedCellId = ref<string>("");
        provide('cell-component-mapping', props.cellMap);

        const cellCount = computed(() => session?.notebook?.cells?.length || 0);

        return {
            session,
            beakerSession,
            notebook,
            selectedCellId,
            cellCount,
        }
    },

    methods: {
        selectCell(cell: string | {id: string}): IBeakerCell {
            if (typeof cell === 'string') {
                this.selectedCellId = cell;
            }
            else {
                this.selectedCellId = cell.id;
            }
            return this.selectedCell;
        },

        selectNextCell(referenceCell?: IBeakerCell): IBeakerCell | null {
            if (referenceCell === undefined) {
                referenceCell = this.selectedCell.cell;
            }
            let cellIndex = this.notebook.cells.indexOf(referenceCell);
            if (cellIndex >= 0) {
                if (cellIndex < this.cellCount - 1) {
                    return this.selectCell(this.notebook.cells[cellIndex+1]);
                }
            }
            else {
                for (const notebookCell of this.notebook.cells) {
                    if (notebookCell.children) {
                        const childIndex = notebookCell.children.indexOf(referenceCell);
                        if (childIndex === -1) {
                            continue;
                        }
                        // If trying to go past last child cell
                        if (childIndex < notebookCell.children.length-1) {
                            // Select the next outer cell, if it exists
                            return this.selectNextCell(notebookCell);
                        }
                        else {
                            //
                            return this.selectCell(notebookCell.children[childIndex+1]);
                        }
                    }
                }
            }
            return null;
        },

        selectPrevCell(referenceCell?: IBeakerCell): IBeakerCell | null {
            let cellIndex = this.notebook.cells.indexOf(this.selectedCell.cell);
            if (cellIndex >= 0) {
                if (cellIndex > 0) {
                    this.selectCell(this.notebook.cells[cellIndex-1]);
                }
            }
            else {
                for (const notebookCell of this.notebook.cells) {
                    // console.log(ch)
                    // if (notebookCell.children)
                    console.log(notebookCell)
                }

            }
            return null;
        },

        insertCellBefore(referenceCell?: IBeakerCell, cellType?: string) {
            if (referenceCell === undefined) {
                referenceCell = this.selectedCell;
            }
            if (cellType === undefined) {
                cellType = "code";
            }
            const index = (referenceCell === undefined ? this.notebook.cells.length-1 : this.notebook.cells.findIndex((cell) => cell === referenceCell.cell));
            // TODO: Switch this to create same type of cell as selected cell
            const newCell = this.session.addCodeCell("");
            this.notebook.moveCell(this.notebook.cells.length -1, index);
            nextTick(() => this.selectCell(newCell));
            return newCell;
        },

        insertCellAfter(referenceCell?: IBeakerCell, cellType?: string) {
            if (referenceCell === undefined) {
                referenceCell = this.selectedCell;
            }
            if (cellType === undefined) {
                cellType = "code";
            }
            const index = (referenceCell === undefined ? this.notebook.cells.length-1 : this.notebook.cells.findIndex((cell) => cell === referenceCell.cell));
            const newCell = this.session.addCodeCell("");
            this.notebook.moveCell(this.notebook.cells.length -1, index + 1);
            nextTick(() => this.selectCell(newCell));
            return newCell;
        },

        removeCell(cell: IBeakerCell): void {
            if (cell === undefined) {
                cell = this.selectedCell;
            }
            const index = this.notebook.cells.findIndex((cellModel) => cellModel === cell.cell);
            if (!this.selectNextCell()) {
                this.selectPrevCell();
            }
            return this.notebook.cutCell(index);
        },
    },

    computed: {
        selectedCell(): typeof BeakerCell {
            return this.beakerSession.findNotebookCellById(this.selectedCellId);
        },
        isEditing(): boolean {
            return true;
        },
    },

    beforeMount() {
        provide('notebook', this);
        if (this.cellCount <= 0) {
            const newCell = this.session.addCodeCell("");
            this.selectCell(newCell.id);
        }
    },
}
</script>


<style lang="scss">
.beaker-notebook {
    display: flex;
    flex: 1;
    flex-direction: column;
    height: 100%;
}

.welcome-placeholder  {
    position: absolute;
    top: 7rem;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: -1;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 90%;
}

</style>
