<template>
    <div class="beaker-notebook">
        <BeakerNotebookToolbar/>
        <NotebookPanel
            :selected-cell="selectedCellId"
            @cell-clicked="selectCell"
            ref="beakerNotebookRef"
        >
            <template #notebook-background>
                <div class="welcome-placeholder">
                    <SvgPlaceholder />
                </div>
            </template>
        </NotebookPanel>
    </div>
</template>

<script lang="tsx">
import { ref, onBeforeMount, onMounted, defineProps, computed, nextTick, provide, inject, defineEmits, defineExpose } from "vue";
import { IBeakerCell, BeakerBaseCell, BeakerSession, BeakerNotebook } from 'beaker-kernel';

import NotebookPanel from '@/components/notebook/BeakerNotebookPanel.vue';
import BeakerNotebookToolbar from "./BeakerNotebookToolbar.vue";
import SvgPlaceholder from '@/components/misc/SvgPlaceholder.vue';
import BeakerCell from '@/components/cell/BeakerCell.vue';
import BeakerSessionComponent from "../session/BeakerSession.vue";

export default {
    props: [
        "cellMap",
    ],
    emits: [
    ],
    components: {
        NotebookPanel,
        BeakerNotebookToolbar
    },

    setup(props, { emit }) {

        const session: BeakerSession = inject('session');
        const beakerSession: typeof BeakerSessionComponent = inject('beakerSession');
        const notebook = ref<BeakerNotebook>(session.notebook);


        // TODO: Clear up session/beakerSession confusion. sessionContext? sessionController?
        const selectedCellId = ref<string>("");
        provide('cell-component-mapping', props.cellMap);

        const somethingNew = 42;

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
        selectCell(cell: string | {id: string}): void {
            if (typeof cell === 'string') {
                this.selectedCellId = cell;
            }
            else {
                this.selectedCellId = cell.id;
            }
        },

        selectNextCell(referenceCell?): string | null {
            if (referenceCell === undefined) {
                referenceCell = this.selectedCell.cell;
            }
            let cellIndex = this.notebook.cells.indexOf(referenceCell);
            if (cellIndex >= 0) {
                if (cellIndex < this.cellCount - 1) {
                    this.selectCell(this.notebook.cells[cellIndex+1]);
                }
            }
            else {
                for (const notebookCell of this.notebook.cells) {
                    console.log(notebookCell)
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

        selectPrevCell(): string | null {
            let cellIndex = this.notebook.cells.indexOf(this.selectedCell.cell);
            console.log(cellIndex);
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
    },

    computed: {
        selectedCell(): typeof BeakerCell {
            return this.beakerSession.findNotebookCellById(this.selectedCellId);
        }

    },

    // /**
    //  * Parses emits by other child components to follow commands that the notebook
    //  * controls.
    //  **/
    // function handleNavAction(action) {
    //     // TODO types
    //     if (action === 'focus-cell') {
    //         focusSelectedCell();
    //     } else if (action === 'select-next-cell') {
    //         if (selectedCellIndex.value === String(cellCount.value - 1)) {
    //             addCodeCell();
    //         } else {
    //             selectNextCell();
    //         }
    //     }
    // }

    // /**
    //  * Splits a combined cell index into component parts.
    //  * Cell indices are in the form of `"1:2"` (representing notebook cell 1, third child)
    //  *
    //  * usage: `const [parent, child] = splitCellIndex("1:2")`
    //  *
    //  * note: child will be `undefined` in the case of `const [parent, child] = splitCellIndex("1")`
    //  * due to assignment destructuring rules
    //  */
    // const splitCellIndex = (index: string): number[] => index.split(":").map((part) => Number(part));

    // const mergeCellIndex = (parent: number, child: number | undefined): string => {
    //     if (typeof(child) !== "undefined") {
    //         return `${parent}:${child}`;
    //     }
    //     return `${parent}`;
    // }

    // const getChildCount = (index: string): number => {
    //     const [parent, child] = splitCellIndex(index);
    //     return session.notebook.cells[parent]?.children?.length || 0
    // }

    // function handleMoveCell(fromIndex: number, toIndex: number) {
    //     //arrayMove(session.notebook.cells, fromIndex, toIndex)
    //     selectCell(toIndex);
    // }

    // function handleKeyboardShortcut(event) {

    //     const { target } = event;

    //     // TODO is there a better way to encapsulate cancelling events
    //     // when writing on textarea/input/code elements ?
    //     const isEditingCode = target.className === 'cm-content'; // codemirror
    //     const isTextArea = target.className.includes('resizeable-textarea');

    //     if (isEditingCode || isTextArea) {
    //         return;
    //     }

    //     beakerNotebookRef.value.handleKeyboardShortcut(event);
    // }

    // const _cellIndex = (cell: number | string | IBeakerCell): string => {
    //     let index = "-1";
    //     if (typeof(cell) === "string") {
    //         index = cell;
    //     }
    //     if (typeof(cell) === "number") {
    //         index = cell.toString();
    //     }
    //     else if (cell instanceof BeakerBaseCell) {
    //         const notebookIndex = session.notebook.cells.indexOf(cell);
    //         index = notebookIndex.toString();

    //         // cell is within a notebook cell's children
    //         if (notebookIndex === -1) {
    //             for (const [notebookIndex, notebookCell] of session.notebook.cells.entries()) {
    //                 const innerIndex = notebookCell?.children?.indexOf(cell);
    //                 if (innerIndex !== -1) {
    //                     index = `${notebookIndex}:${innerIndex}`;
    //                     break;
    //                 }
    //             }
    //         }
    //     }
    //     return index;
    // }


    // const _getCell = (cell: string | IBeakerCell): IBeakerCell => {
    //     const index = _cellIndex(cell);
    //     const [parent, child] = splitCellIndex(index);
    //     if (typeof(child) !== "undefined") {
    //         return session.notebook.cells[parent]?.children[child];
    //     }
    //     return session.notebook.cells[parent];
    // }

    // const commonSelectAction = (event): boolean => {
    //     const { target } = event;

    //     const isEditingCode = target.className === 'cm-content'; // codemirror
    //     const isTextArea = target.className.includes('resizeable-textarea');

    //     if (isEditingCode || isTextArea) {
    //         return false;
    //     }

    //     return true;
    // };

    // function focusSelectedCell() {
    //     if (!beakerNotebookRef.value){
    //         return;
    //     }
    //     const elem = beakerNotebookRef.value.querySelector('.beaker-cell.selected');
    //     if (typeof(elem) !== "undefined" && elem !== null) {
    //         elem.focus();
    //     }
    // }

    // const selectNextCell = (event?) => {
    //     if (event && !commonSelectAction(event)) {
    //         return;
    //     }

    //     const currentIndex = selectedCellIndex.value;
    //     const childCount = getChildCount(currentIndex);
    //     const [parent, child] = splitCellIndex(currentIndex);
    //     // TODO should we wrap around? Should we auto-add a new cell?
    //     if (parent === cellCount.value - 1) {
    //         return;
    //     }

    //     // since children are 0-indexed, consider a parent selector as "child -1" for purpose of incrementing
    //     const childIndex = typeof(child) === "undefined" ? -1 : child;
    //     if (childCount > 0 && childIndex < childCount - 1) {
    //         selectCell(`${parent}:${childIndex + 1}`);
    //     } else {
    //         selectCell(`${parent + 1}`);
    //     }

    //     nextTick(() => {
    //         focusSelectedCell();
    //     });

    //     if (event) {
    //         event.preventDefault();
    //     }
    // };

    // const selectPreviousCell = (event?) => {

    //     if (event && !commonSelectAction(event)) {
    //         return;
    //     }

    //     const currentIndex = selectedCellIndex.value;
    //     const childCount = getChildCount(currentIndex);
    //     const [parent, child] = splitCellIndex(currentIndex);

    //     if (parent === 0) {
    //         return;
    //     }

    //     if (childCount > 0 && child > 0) {
    //         selectCell(`${parent}:${child - 1}`);
    //     } else {
    //         // select last child of above cell if present
    //         const target = `${parent - 1}`;
    //         const targetChildCount = getChildCount(target);
    //         if (targetChildCount > 0) {
    //             selectCell(`${target}:${targetChildCount - 1}`)
    //         } else {
    //             selectCell(target);
    //         }
    //     }

    //     nextTick(() => {
    //         focusSelectedCell();
    //     });

    //     if (event) {
    //         event.preventDefault();
    //     }
    // };

    // const addCell = (toIndex) => {
    //     beakerNotebookRef.value.addCell(toIndex);
    //     // if (typeof toIndex !== 'number') {
    //     //     toIndex = selectedCellIndex.value + 1;
    //     // }
    //     // const newCell = new BeakerCodeCell({
    //     //     cell_type: "code",
    //     //     source: "",
    //     //     metadata: {},
    //     //     outputs: [],
    //     // });
    //     // session.notebook.insertCell(newCell, toIndex);

    //     // // arrayMove(session.notebook.cells, cellCount.value - 1, toIndex)

    //     // selectCell(newCell);

    //     // nextTick(() => {
    //     //     focusSelectedCell();
    //     // });
    // }

    // const addCodeCell = (toIndex?: number) => {
    //     const newCell = session.addCodeCell("");

    //     if (typeof toIndex !== 'number') {
    //         const [parent, child] = splitCellIndex(selectedCellIndex.value);
    //         toIndex = parent + 1;
    //     }
    //     // arrayMove(session.notebook.cells, cellCount.value - 1, toIndex)

    //     selectCell(newCell);

    //     nextTick(() => {
    //         focusSelectedCell();
    //     });
    // }

    // const addMarkdownCell = (toIndex?: number) => {
    //     const newCell = session.addMarkdownCell("");

    //     if (typeof toIndex !== 'number') {
    //         const [parent, child] = splitCellIndex(selectedCellIndex.value);
    //         toIndex = parent + 1;
    //     }
    //     // arrayMove(session.notebook.cells, cellCount.value - 1, toIndex)

    //     selectCell(newCell);

    //     nextTick(() => {
    //         notebookCellsRef.value[notebookCellsRef.value.length - 1].enter();
    //         focusSelectedCell();
    //     });
    // }

    // const runCell = (cell?: string | IBeakerCell) => {
    //     beakerNotebookRef.value.runCell(cell);
    // }

    // const removeCell = () => {
    //     beakerNotebookRef.value.removeCell();
    //     // session.notebook.removeCell(selectedCellIndex.value);

    //     // // Always keep at least one cell. If we remove the last cell, replace it with a new empty codecell.
    //     // if (cellCount.value === 0) {
    //     //     session.addCodeCell("");
    //     // }
    //     // // Fixup the selection if we remove the last item.
    //     // if (selectedCellIndex.value >= cellCount.value) {
    //     //     selectedCellIndex.value = cellCount.value - 1;
    //     // }
    // };

    // const resetNB = async () => {
    //     await session.reset();
    //     if (cellCount.value === 0) {
    //         session.addCodeCell("");
    //     }
    // };

    // function toggleContextSelection() {
    //     contextSelectionOpen.value = !contextSelectionOpen.value;
    // }


    // function scrollBottomCellContainer() {
    //     if (beakerNotebookRef.value) {
    //         beakerNotebookRef.value.scrollBottomCellContainer();
    //     }
    // }

    beforeMount() {
        provide('notebook', this);
        if (this.cellCount <= 0) {
            // const session: BeakerSession = inject('session');
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
