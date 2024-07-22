<template>
    <div class="beaker-notebook">
        <slot></slot>
    </div>
</template>

<script lang="tsx">
import { defineComponent, ref, computed, nextTick, provide, inject } from "vue";
import { IBeakerCell, BeakerSession, BeakerNotebook } from 'beaker-kernel';
import { BeakerSessionComponent, BeakerSessionComponentType } from "../session/BeakerSession.vue";

export interface IBeakerCellComponent {
    execute: () => null;
    enter: () => null;
    exit: () => null;
    clear: () => null;
}

export const BeakerNotebookComponent = defineComponent({
    props: [
        "cellMap",
    ],

    setup(props) {

        const session: BeakerSession = inject('session');
        const beakerSession = inject<BeakerSessionComponentType>('beakerSession');
        const notebook = ref<BeakerNotebook>(session.notebook);

        // TODO: Clear up session/beakerSession confusion. sessionContext? sessionController?
        const selectedCellId = ref<string | null>(null);
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
        selectCell(cell: string | {id: string}, enter=false): string {
            let newCellId;
            if (typeof cell === 'string') {
                newCellId = cell;
            }
            else {
                newCellId = cell.id;
            }
            if (this.selectedCellId !== newCellId) {
                this.selectedCellId = newCellId
                nextTick(() => {
                    if (enter) {
                        this.selectedCell()?.enter();
                    }
                    else {
                        this.selectedCell()?.exit();
                    }
                });
            }
            return this.selectedCellId;
        },

        // This can't/shouldn't be a computed property because it information about the selected cell can change
        // without the dependencies in the function changing.
        selectedCell(): IBeakerCell {
            return this.beakerSession.findNotebookCellById(this.selectedCellId);
        },

        selectNextCell(referenceCell?: IBeakerCell, enter=false): IBeakerCell | null {
            if (referenceCell === undefined) {
                referenceCell = this.selectedCell().cell;
            }
            let cellIndex = this.notebook.cells.indexOf(referenceCell);
            if (cellIndex >= 0) {
                if (cellIndex < this.cellCount - 1) {
                    return this.selectCell(this.notebook.cells[cellIndex+1], enter);
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
                            return this.selectCell(notebookCell.children[childIndex+1], enter);
                        }
                    }
                }
            }
            return null;
        },

        selectPrevCell(referenceCell?: IBeakerCell, enter=false): IBeakerCell | null {
            let cellIndex = this.notebook.cells.indexOf(this.selectedCell().cell);
            if (cellIndex >= 0) {
                if (cellIndex > 0) {
                    this.selectCell(this.notebook.cells[cellIndex-1], enter);
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

        insertCellBefore(referenceCell?: IBeakerCell, cellType?: string, enter=false) {
            if (referenceCell === undefined) {
                referenceCell = this.selectedCell();
            }
            if (cellType === undefined) {
                cellType = "code";
            }
            const index = (referenceCell === undefined ? this.notebook.cells.length-1 : this.notebook.cells.findIndex((cell) => cell === referenceCell.cell));
            // TODO: Switch this to create same type of cell as selected cell
            const newCell = this.session.addCodeCell("");
            this.notebook.moveCell(this.notebook.cells.length -1, index);
            nextTick(() => this.selectCell(newCell, enter));
            return newCell;
        },

        insertCellAfter(referenceCell?: IBeakerCell, cellType?: string, enter=false) {
            if (referenceCell === undefined) {
                referenceCell = this.selectedCell();
            }
            if (cellType === undefined) {
                cellType = "code";
            }
            const index = (referenceCell === undefined ? this.notebook.cells.length-1 : this.notebook.cells.findIndex((cell) => cell === referenceCell.cell));
            const newCell = this.session.addCodeCell("");
            this.notebook.moveCell(this.notebook.cells.length -1, index + 1);
            nextTick(() => this.selectCell(newCell, enter));
            return newCell;
        },

        removeCell(cell?: IBeakerCell): void {
            if (cell === undefined) {
                cell = this.selectedCell();
            }
            const index = this.notebook.cells.findIndex((cellModel) => cellModel === cell.cell);
            if (!this.selectNextCell()) {
                this.selectPrevCell();
            }
            return this.notebook.cutCell(index);
        },
    },

    computed: {
    },

    beforeMount() {
        provide('notebook', this);
        if (this.cellCount === 0) {
            const newCell = this.session.addCodeCell("");
        }
    },

    mounted() {
        if (!this.selectedCell()) {
            this.selectCell(this.notebook.cells[0].id);
        }
    }
});

export type BeakerNotebookComponentType = InstanceType<typeof BeakerNotebookComponent>;

export default BeakerNotebookComponent;

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
