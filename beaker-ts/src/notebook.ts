import * as nbformat from '@jupyterlab/nbformat';
import * as messages from '@jupyterlab/services/lib/kernel/messages';
import { JSONObject, PartialJSONValue } from '@lumino/coreutils';
import { IShellFuture } from '@jupyterlab/services/lib/kernel/kernel';
import { v4 as uuidv4 } from 'uuid';

import { BeakerSession } from './session';
import { IBeakerFuture, BeakerCellFuture, BeakerCellFutures } from './util';


export interface IBeakerHeader extends messages.IHeader {
    msg_type: any;
}

export interface IBeakerShellMessage extends messages.IShellMessage {
    header: IBeakerHeader;
    channel: "shell";
    content: JSONObject;
}

export interface IBeakerIOPubMessage extends messages.IIOPubMessage {
    header: IBeakerHeader;
    channel: "iopub";
    content: any;
}

export type BeakerCellStatus = messages.Status | "awaiting_input";

export type BeakerCellExecutionStatus = IBeakerCellExecutionStatusPlain | IBeakerCellExecutionStatusPending | IBeakerCellExecutionStatusOk | IBeakerCellExecutionStatusError;

export interface IBeakerCellExecutionStatusPlain {
    status: "none" | "modified" | "abort";
}

export interface IBeakerCellExecutionStatusPending {
    status: "pending";
    checkpoint_index?: number;
}

export interface IBeakerCellExecutionStatusOk {
    status: "ok"
    checkpoint_index?: number;
}
export interface IBeakerCellExecutionStatusError {
    status: "error";
    ename: string;
    evalue: string;
    traceback: string[];
}

export type BeakerCellType = nbformat.CellType | string | 'query';

export class BeakerBaseCell implements nbformat.IBaseCell {
    // Override index type to allow methods to be defined on the class
    private IPYNB_KEYS = ["cell_type", "source", "metadata", "id", "attachments",
                  "outputs", "execution_count"];

    [key: string]: any;
    cell_type: BeakerCellType;
    metadata: Partial<nbformat.ICellMetadata>;
    source: nbformat.MultilineString;
    status: BeakerCellStatus;
    children: BeakerBaseCell[];

    constructor() {
        this.status = "idle";
        this.last_execution = {status: "none"};
        this.children = [];
    }

    public reset_execution_state(): void {
        this.last_execution = {status: "modified"};
    }

    public fromJSON(obj: any) {
        Object.keys(obj).forEach((key) => {
            this[key] = obj[key];
        })
    }

    public toJSON() {
        return {...this};
    }

    public fromIPynb(obj: any) {
        Object.keys(obj).forEach((key) => {
            this[key] = obj[key];
        })
    }

    public toIPynb() {
        const output = {};
        for (const key of Object.keys(this)) {
            if (this.IPYNB_KEYS.includes(key)) {
                output[key] = this[key];
            }
        }
        return(output);
    }
}

export interface IBeakerQueryEvent extends JSONObject {
    type: "thought" | "response" | "user_question" | "user_answer" | "error" | "code_cell" | "abort";
    content: string | PartialJSONValue;
};

export interface IQueryCell extends nbformat.IBaseCell {
    cell_type: 'query';
    id?: string;
    events: IBeakerQueryEvent[];
}

export class BeakerRawCell extends BeakerBaseCell implements nbformat.IRawCell {
    declare cell_type: 'raw';
    id?: string;
    attachments?: nbformat.IAttachments;
    declare metadata: Partial<nbformat.IRawCellMetadata>;

    constructor(content: nbformat.ICell) {
        super();
        Object.keys(content).forEach((key) => {this[key] = content[key] });
        if (this.id === undefined) {
            this.id = uuidv4();
        }
    }

    public execute(session: BeakerSession): IBeakerFuture | null {
        return null
    };
}

export class BeakerCodeCell extends BeakerBaseCell implements nbformat.ICodeCell {
    declare cell_type: 'code';
    id?: string;
    outputs: nbformat.IOutput[];
    execution_count: nbformat.ExecutionCount;
    declare metadata: Partial<nbformat.ICodeCellMetadata>;
    last_execution?: BeakerCellExecutionStatus;
    busy?: boolean;

    constructor(content: nbformat.ICell) {
        super();
        Object.keys(content).forEach((key) => {this[key] = content[key] });
        if (this.id === undefined) {
            this.id = uuidv4();
        }
        if (this.execution_count === undefined) {
            this.execution_count = null;
        }
        this.busy = false;
        if (Array.isArray(this.source)) {
            this.source = this.source.join("\n");
        }
    }

    public execute(session: BeakerSession, syntheticFuture: BeakerCellFuture = undefined): IBeakerFuture | null {
        this.busy = true;

        var future: BeakerCellFuture | IShellFuture;
        this.outputs.splice(0, this.outputs.length);
        if (syntheticFuture !== undefined) {
            future = syntheticFuture;
        }
        else {
            future = session.sendBeakerMessage(
                "execute_request",
                {
                    code: this.source,
                    silent: false,
                    store_history: true,
                    user_expressions: {},
                    allow_stdin: true,
                    stop_on_error: false,
                }
            );
            future.onIOPub = (msg: IBeakerIOPubMessage) => BeakerCellFutures.handleIOPub(msg, this);
            future.onReply = (msg: IBeakerShellMessage) => BeakerCellFutures.handleReply(msg, this);
        }
        return future;
    }

    public rollback(session: BeakerSession): IBeakerFuture | null {
        if (this?.last_execution?.status === "ok") {
            const future = session.executeAction(
                "rollback",
                {
                    checkpoint_index: this.last_execution.checkpoint_index
                }
            );
            // Treat rolling back like an execution as it may fail
            this.busy = true;

            // Clear outputs and children when rollback completes
            future.done.then((reply_msg: messages.IExecuteReplyMsg) => {
                if (reply_msg.content.status === "ok") {
                    this.busy = false;
                    this.last_execution = {"status": "none"};
                    this.execution_count = null;
                    this.outputs.splice(0, this.outputs.length);
                    this.children.splice(0, this.children.length);
                }
                else if (reply_msg.content.status === "error") {
                    this.last_execution = reply_msg.content;
                    this.outputs.push({...reply_msg.content, output_type: "error"})
                }
            });
            return future;
        }
        return null;
    };
}

export class BeakerMarkdownCell extends BeakerBaseCell implements nbformat.IMarkdownCell {
    declare cell_type: 'markdown';
    id?: string;
    attachments?: nbformat.IAttachments;

    constructor(content: nbformat.ICell) {
        super();
        Object.keys(content).forEach((key) => {this[key] = content[key] });
        if (this.id === undefined) {
            this.id = uuidv4();
        }
    }

    public execute(session: BeakerSession): IBeakerFuture | null {
        // TODO: Replace this with code to render markdown.
        return null;
    };
}

export class BeakerQueryCell extends BeakerBaseCell implements IQueryCell {
    declare cell_type: 'query';
    id?: string;
    events: IBeakerQueryEvent[];

    _current_input_request_message: messages.IInputRequestMsg;

    constructor(content: nbformat.ICell) {
        super();
        this.events = [];
        Object.keys(content).forEach((key) => {this[key] = content[key] });
        if (this.id === undefined) {
            this.id = uuidv4();
        }
    }

    public execute(session: BeakerSession): IBeakerFuture | null {
        this.events.splice(0, this.events.length);
        this.children.splice(0, this.children.length);

        const handleIOPub = async (msg: IBeakerIOPubMessage) => {
            const msg_type = msg.header.msg_type;
            const content = msg.content;
            if (msg_type === "status") {
                this.status = content.execution_state;
            }
            else if (msg_type === "llm_thought") {
                this.events.push({
                    type: "thought",
                    content: content.thought,
                });
            }
            else if (msg_type === "llm_response" && content.name === "response_text") {
                this.events.push({
                    type: "response",
                    content: content.text,
                });
            }
            else if (msg_type === "code_cell") {
                const nb = session.notebook;
                const codeCell = new BeakerCodeCell({
                    cell_type: "code",
                    source: content.code,
                    metadata: {
                        parent_cell: this.id,
                    },
                    outputs: [],
                });

                const queryCellIndex = nb.cells.findIndex((cell) => (cell.id === this.id));
                if (queryCellIndex >= 0) {
                    session.notebook.cells.splice(queryCellIndex + 1, 0, codeCell);
                }
                else {
                    nb.addCell(codeCell);
                }
            }
            else if (msg_type === "add_child_codecell") {
                const autoexecute = content.autoexecute;
                const codeCell = new BeakerCodeCell({
                    cell_type: "code",
                    source: content.code,
                    metadata: {
                        parent_cell: this.id,
                    },
                    outputs: [],
                    busy: true,
                });
                codeCell.last_execution = {
                    status: "pending",
                    checkpoint_index: content.checkpoint_index,
                }
                this.children.push(codeCell);
                this.events.push({
                    type: "code_cell",
                    content: {
                        id: codeCell.id,
                        index: this.children?.length - 1
                    },
                });

                const reactiveCell = this.children[this.children.length - 1] as BeakerCodeCell;
                if (autoexecute && content.execute_request_msg) {
                    const executeRequest = content.execute_request_msg;
                    const future = new BeakerCellFuture(
                        executeRequest,  // Message that is presumably sent
                        true,  // expectReply
                        true,  // disposeOnDone
                        session.kernel,  // kernel
                        reactiveCell,  // relatedCodecell
                    );
                }
            }
            else if (msg_type == "update_child_codecell") {
                const cellId = content.id;
                const cell = this.children.find((value) => (value.id === cellId));
                if (cell === undefined || cell === null) {
                    console.log("Can't find cell");
                    throw Error("Cell to be updated not found ")
                }

                cell.execution_count = content.execution_count;
                let status : BeakerCellExecutionStatus = {
                    status: content.execution_status
                }

                if (content.execution_status === "error") {
                    // TODO: align to message output, placeholder
                    const error_details = {
                        ename: msg.content.ename,
                        evalue: msg.content.evalue,
                        traceback: msg.content.traceback,
                    };
                    cell.outputs.push({
                        output_type: "error",
                        ...error_details,
                    });
                    status = {...status, ...error_details};
                }
                else if (status.status === "ok") {
                    status = {...status, checkpoint_index: content.checkpoint_index};
                    cell.outputs.push({
                        output_type: "execute_result",
                        data: {
                            "text/plain": content.execution_return
                        }
                    });
                }
                cell.last_execution = status;
            }
        };

        const handleStdin = async (msg: messages.IStdinMessage) => {
            if (messages.isInputRequestMsg(msg)) {
                this.events.push({
                    type: "user_question",
                    content: msg.content.prompt,
                });
                this.status = "awaiting_input";
                this._current_input_request_message = msg;
            }
        }

        const handleReply = async (msg: messages.IExecuteReplyMsg) => {
            if (msg.content.status === "ok") {
                this.last_execution = {
                    status: "ok",
                };
            }
            else if (msg.content.status === "error") {
                const error_details = {
                    ename: msg.content.ename,
                    evalue: msg.content.evalue,
                    traceback: msg.content.traceback,
                };
                this.last_execution = {
                    status: "error",
                    ...error_details
                };
                this.events.push({
                    type: "error",
                    content: msg.content.evalue,
                });
            }
            else if (msg.content.status === "abort") {
                this.last_execution = {
                    status: "abort",
                };
                this.events.push({
                    type: "abort",
                    content: "Request aborted",
                });
            }
        };

        const future = session.sendBeakerMessage(
            "llm_request",
            {
                request: this.source
            }
        );
        future.onIOPub = handleIOPub;
        future.onStdin = handleStdin;
        future.onReply = handleReply;
        return future;
    };

    public respond(response: string, session: BeakerSession) {
        // Only handle if we're awaiting input
        if (this.status !== "awaiting_input") {
            return;
        }

        this.events.push({
            type: "user_answer",
            content: response,
        });

        // Send the reply to the kernel
        session.kernel.sendInputReply(
            {
                "value": response,
                "status": "ok",
            },
            this._current_input_request_message.header,
        );

        //cleanup
        this.status = "busy";
        this._current_input_request_message = undefined;
    }

    public toMarkdownCell() {
        const renderedMarkdownLines = [`# ${this.source}\n`];
        this.events.forEach((event) => {
            if (event.type === "thought") {
                renderedMarkdownLines.push(`> Thought: ${event.content}\n> `);
            }
            else if (event.type === "response") {
                renderedMarkdownLines.push(`**${event.content}**`);
            }
            else if (event.type === "user_question") {
                renderedMarkdownLines.push(`*Beaker asks:* ${event.content}\n`);
            }
            else if (event.type === "user_answer") {
                renderedMarkdownLines.push(`*The user responds:* ${event.content}\n`);
            }
        });
        const renderedMarkdown = renderedMarkdownLines.join("\n");
        const metadata = {
            ...this.metadata,
            beaker_cell_type: "query",
            prompt: this.source,
            events: this.events,
        }
        return new BeakerMarkdownCell(
            {
                cell_type: "markdown",
                id: this.id,
                source: renderedMarkdown,
                metadata: metadata,
            }
        );
    }

    // public fromJSON(obj: any) {
    //     if (this.metadata.beaker_cell_type !== "query") {
    //         throw TypeError("Cell is trying to be parsed as a query cell, but doesn't have the required metadata.")
    //     }
    //     this.source = obj.metadata.prompt;
    //     this.events = obj.metadata.events;
    // }

    // public toJSON() {
    //     return this.toMarkdownCell();
    // }

    public fromIPynb(obj: any) {
        if (this.metadata.beaker_cell_type !== "query") {
            throw TypeError("Cell is trying to be parsed as a query cell, but doesn't have the required metadata.")
        }
        this.source = obj.metadata.prompt;
        this.events = obj.metadata.events;

    }

    public toIPynb() {
        // TODO: Is this modifying the cells in memory, if so, is this causing problems?
        const taggedChildren = this.children?.map((cell) => {
            cell.metadata.beaker_child_of = this?.id;
            return cell.toIPynb();
        });
        return [this.toMarkdownCell().toIPynb(), ...taggedChildren];
    }
}

export type IBeakerCell = BeakerCodeCell | BeakerMarkdownCell | BeakerRawCell | nbformat.IUnrecognizedCell;

export class BeakerNotebookContent implements nbformat.INotebookContent {

    [key: string]: PartialJSONValue | undefined;
    nbformat: number;
    nbformat_minor: number;
    metadata: nbformat.INotebookMetadata;
    cells: IBeakerCell[];
}

export class BeakerNotebook {
    constructor() {

        this.content = {
            nbformat: 4,
            nbformat_minor: 5,
            cells: [],
            metadata: {
                "kernelspec": {
                    "display_name": "Beaker Kernel",
                    "name": "beaker",
                    "language": "beaker",
                   },
                   "language_info": this.subkernelInfo,
            },
        }

        // Using a Proxy to get around issues with reactivity in getters/setters
        this.cells = new Proxy(this.content.cells, {});
    }

    public toJSON() {
        this.content.metadata.language_info = this.subkernelInfo;
        return {...this.content};
    }

    public fromJSON(obj: any) {
        Object.keys(obj).forEach((key) => {
            this.content[key] = obj[key];
        })
    }

    public loadFromIPynb(obj: any) {
        this.content.nbformat = obj.nbformat;
        this.content.nbformat_minor = obj.nbformat_minor;
        const cellList = obj.cells.map((cell: IBeakerCell) => {
            if (cell.cell_type === "raw") {
                return new BeakerRawCell(cell);
            }
            else if (cell.cell_type === "code") {
                return new BeakerCodeCell(cell);
            }
            else if (cell.metadata.beaker_cell_type === "query") {
                return new BeakerQueryCell({
                    cell_type: "query",
                    id: cell.id,
                    source: cell.metadata.prompt as nbformat.MultilineString,
                    events: cell.metadata.events,
                    metadata: cell.metadata,
                });
            }
            else if (cell.cell_type === "markdown") {
                return new BeakerMarkdownCell(cell);
            }
        });

        let cellMap: {[uuid: string]: BeakerBaseCell} = {};
        cellList.forEach((cell: BeakerBaseCell) => {
            cellMap[cell.id] = cell;
        });

        let i = 0;
        while (i < cellList.length) {
            const cell = cellList[i];
            if (typeof(cell.metadata.beaker_child_of) !== "undefined") {
                cellMap[cell.metadata.beaker_child_of].children.push(cellList.splice(i, 1)[0]);
            }
            else {
                i++;
            }
        }

        this.cells.splice(
            0,
            this.cells.length,
            ...cellList
        );
        this.content.metadata = obj.metadata;
    }

    public toIPynb() {
        this.content.metadata.language_info = this.subkernelInfo;
        return {
            nbformat: this.content.nbformat,
            nbformat_minor: this.content.nbformat_minor,
            cells: this.content.cells.flatMap((cell: BeakerBaseCell) => cell.toIPynb()),
            metadata: this.content.metadata,
        }
    }

    public addCell(cell: IBeakerCell | nbformat.ICell) {
        this.cells.push(cell);
    }

    public removeCell(index: number) {
        this.cells.splice(index, 1);
    }

    public setSubkernelInfo(sessionInfo: any) {
        this.subkernelInfo = {
            "name": sessionInfo.subkernel,
            "display_name": sessionInfo.language,
        }
    };

    private content: BeakerNotebookContent;
    public cells: IBeakerCell[];
    private subkernelInfo: nbformat.ILanguageInfoMetadata;
}
