import { defineComponent, ref, computed, nextTick, provide, inject, DefineComponent } from "vue";
import { IBeakerCell, BeakerSession, BeakerNotebook, BeakerMarkdownCell, BeakerCodeCell, BeakerQueryCell, BeakerRawCell } from 'beaker-kernel/src';

declare const BeakerNotebookComponent: DefineComponent<any, any, any, any>;

export type BeakerNotebookComponentType = InstanceType<typeof BeakerNotebookComponent>;

export default BeakerNotebookComponent;
