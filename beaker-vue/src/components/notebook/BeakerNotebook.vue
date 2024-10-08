<template>
    <div class="beaker-notebook">
        <slot></slot>
    </div>
</template>

<script lang="tsx">
import { defineComponent, ref, computed, nextTick, provide, inject, DefineComponent } from "vue";
import { IBeakerCell, BeakerSession, BeakerNotebook, BeakerMarkdownCell, BeakerCodeCell, BeakerQueryCell, BeakerRawCell } from 'beaker-kernel';
import { IBeakerCellComponent, type BeakerSessionComponentType} from "../session/BeakerSession.vue";
import scrollIntoView from 'scroll-into-view-if-needed';

export const BeakerNotebookComponent: DefineComponent<any, any, any>  = defineComponent({
    props: [
        "cellMap",
        "noEmptyStartingCell"
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
        selectCell(cell: string | {id: string}): string {
            if (cell === undefined) {
                return "";
            }

            let newCellId;
            if (typeof cell === 'string') {
                newCellId = cell;
            }
            else {
                newCellId = cell.id;
            }
            if (this.selectedCellId !== newCellId) {
                this.selectedCellId = newCellId
            }

            nextTick(() => {
                this.scrollCellIntoView(this.selectedCell());
            })

            return this.selectedCellId;
        },

        scrollCellIntoView(cell: IBeakerCellComponent): void {
            const el = cell?.$?.vnode?.el;
            if (!el) {
                return;
            }
            const target = el.closest('.beaker-cell') ?? el;
            scrollIntoView(target, {
                scrollMode: "if-needed",
                block: "nearest",
                inline: "nearest",
            })
        },

        // This can't/shouldn't be a computed property because it information about the selected cell can change
        // without the dependencies in the function changing.
        selectedCell(): IBeakerCellComponent  {
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
                        if (childIndex <= notebookCell.children.length-1) {
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
            let index = (referenceCell === undefined ? this.notebook.cells.length-1 : this.notebook.cells.findIndex((cell) => cell === referenceCell.cell));
            // if reference cell is a child
            const parentId = referenceCell?.cell?.metadata?.beaker_child_of;
            if (index === -1 && parentId) {
                index = this.notebook.cells.findIndex(cell => cell.id === parentId);
            }
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

        convertCellType(cell: IBeakerCell, cellType: string) {
            const cellIndex = this.notebook.cells.indexOf(cell);
            if (cellIndex === -1) {
                console.warn("attempted to convert cell not found in parent cell in place; cell not found");
                return;
            }
            if (!Object.keys(this.cellMap).includes(cellType)) {
                console.warn("invalid cell type provided for conversion target");
                return;
            }
            const newCell = new this.cellMap[cellType].modelClass({...cell});
            newCell.cell_type = cellType;
            this.notebook.cells.splice(cellIndex, 1, newCell);
        }
    },

    computed: {
    },

    beforeMount() {
        provide('notebook', this);
        if (this.cellCount === 0) {
            if (this.noEmptyStartingCell) {
                return;
            }
            const newCell = this.session.addCodeCell("");
        }
    },

    mounted() {
        if (this.noEmptyStartingCell) {
            return;
        }
        if (!this.selectedCell()) {
            nextTick(() => {
                if (this.notebook.cells.length > 0) {
                    this.selectCell(this.notebook.cells[0].id);
                }
            });
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
