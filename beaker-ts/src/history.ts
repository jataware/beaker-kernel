import * as nbformat from '@jupyterlab/nbformat';


export interface IBeakerHistoryEvent {
    kernel_id: string;
    kernel_slug: string;
    context_slug: string;
    creation_time: Date;
}

export interface IBeakerHistoryExecutionEvent extends IBeakerHistoryEvent {
    cell_id: string;
    execution_time: Date;
    execution_duration: number;

    execution_id: number;
    source: nbformat.MultilineString;
    result: any;
    stdin: nbformat.MultilineString;
    stderr: nbformat.MultilineString;
    success: boolean;
}

export interface IBeakerHistoryQueryEvent extends IBeakerHistoryEvent {
    cell_id: string;
    execution_time: Date;
    execution_duration: number;

    source: nbformat.MultilineString;
    thoughts: string[];
    result: nbformat.MultilineString;
}

export interface IBeakerHistory {
    sessionId: string;
    events: IBeakerHistoryEvent[];
}
