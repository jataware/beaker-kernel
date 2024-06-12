import * as nbformat from '@jupyterlab/nbformat';
import { Kernel } from '@jupyterlab/services/lib/kernel';
import * as messages from '@jupyterlab/services/lib/kernel/messages';
import { JSONObject, PartialJSONValue } from '@lumino/coreutils';
import { v4 as uuidv4 } from 'uuid';

import { BeakerSession } from './session';
import { IBeakerFuture } from './util';
import { MenuSvg } from '@jupyterlab/ui-components';

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

export type BeakerCellExecutionStatus = IBeakerCellExecutionStatusPlain | IBeakerCellExecutionStatusOk | IBeakerCellExecutionStatusError 

export interface IBeakerCellExecutionStatusPlain {
    status: "none" | "modified" | "pending" | "abort";
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
    children?: BeakerBaseCell[];

    constructor() {
        this.status = "idle";
        this.last_execution = {status: "none"};
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


    constructor(content: nbformat.ICell) {
        super();
        Object.keys(content).forEach((key) => {this[key] = content[key] });
        if (this.id === undefined) {
            this.id = uuidv4();
        }
        if (this.execution_count === undefined) {
            this.execution_count = null;
        }
        if (Array.isArray(this.source)) {
            this.source = this.source.join("\n");
        }
    }

    public execute(session: BeakerSession): IBeakerFuture | null {
        const handleIOPub = (msg: IBeakerIOPubMessage): void => {
            const msg_type = msg.header.msg_type;
            const content = msg.content;
            if (msg_type === "status") {
                this.status = content.execution_state;
            }
            else if (msg_type === "execute_result") {
                if (content.execution_count) {
                    this.execution_count = content.execution_count;
                }
                this.outputs.push({
                    output_type: "execute_result",
                    ...content
                })
            }
            else if (msg_type === "stream") {
                this.outputs.push({
                    output_type: "stream",
                    ...content
                })
            }
            else if (msg_type === "display_data") {
                this.outputs.push({
                    output_type: "display_data",
                    ...content
                })
            }
        };

        const handleReply = async (msg: messages.IExecuteReplyMsg) => {
            if (msg.content.status === "ok") {
                this.last_execution = {status: "ok"};
                this.execution_count = msg.content.execution_count;
            }
            else if (msg.content.status === "error") {
                this.execution_count = msg.content.execution_count;
                const error_details = {
                    ename: msg.content.ename,
                    evalue: msg.content.evalue,
                    traceback: msg.content.traceback,
                };
                this.last_execution = {
                    status: "error",
                    ...error_details
                };
                this.outputs.push({
                    output_type: "error",
                    ...error_details
                });
            }
            else if (msg.content.status === "abort") {
                this.execution_count = msg.content.execution_count;
                const error_details = {
                    ename: "Execution aborted",
                    evalue: "Execution aborted",
                    traceback: [],
                };
                this.last_execution = {
                    status: "error",
                    ...error_details,
                };
                this.outputs.push({
                    output_type: "error",
                    content: error_details,
                });
            }
        };

        this.outputs.splice(0, this.outputs.length);
        const future = session.sendBeakerMessage(
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
        future.onIOPub = handleIOPub;
        future.onReply = handleReply;
        return future;
    }

    public rollback(session: BeakerSession): IBeakerFuture | null {
        if (this?.last_execution?.status === "ok") {
            console.log(this.last_execution.checkpoint_index);
            const future = session.executeAction(
                "rollback",
                {
                    checkpoint_index: this.last_execution.checkpoint_index
                }
            );
            this.last_execution = {"status": "none"};
            this.execution_count = null;
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
        return null
    };
}

export class BeakerQueryCell extends BeakerBaseCell implements IQueryCell {
    declare cell_type: 'query';
    id?: string;
    events: IBeakerQueryEvent[];

    _current_input_request_message: messages.IInputRequestMsg;

    constructor(content: nbformat.ICell) {
        super();
        Object.keys(content).forEach((key) => {this[key] = content[key] });
        this.events = this.events || [];
        this.children = this.children || [];
        if (this.id === undefined) {
            this.id = uuidv4();
        }
    }

    public execute(session: BeakerSession): IBeakerFuture | null {
        this.events = [];

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
                })
            }
            else if (msg_type === "llm_response" && content.name === "response_text") {
                this.events.push({
                    type: "response",
                    content: content.text,
                })
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
            else if (msg_type == "add_child_codecell") {
                const codeCell = new BeakerCodeCell({
                    cell_type: "code",
                    source: content.code,
                    metadata: {
                        parent_cell: this.id,
                        execution_id: content.execution_id
                    },
                    outputs: [],
                });
                this.children.push(codeCell);
                this.events.push({
                    type: "code_cell",
                    content: {
                        id: codeCell.id,
                        index: this.children?.length - 1
                    },
                });

            }
            else if (msg_type == "update_child_codecell") {
                for (const cell of this.children) {
                    if (cell.metadata?.execution_id == content.execution_id) {
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
                        break;
                    }
                }
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

        // attach children to parents: partition before attaching in one pass
        // such that there's no dangling indices while removing elements from a list by iteration
        //
        // this is entirely a no-op if no cells are tagged as children; legacy notebooks of all parent cells are unaffected
        const [parentCells, childCells]: [IBeakerCell[], IBeakerCell[]] = cellList.reduce(
            (partitions: IBeakerCell[][], cell: IBeakerCell) => {
                const isChild = (cell: IBeakerCell) => typeof(cell.metadata.beaker_child_of) !== "undefined";
                partitions[isChild(cell) ? 1 : 0].push(cell);
                return partitions;
            }, [[], []]
        );
        // avoid the need to search parents every iteration when attaching
        const childMap: {[parent_uuid: string]: IBeakerCell[]} = childCells.reduce((mapping, cell) => {
            const parent_uuid = String(cell.metadata.beaker_child_of);
            return {
                [parent_uuid]: [...(mapping[parent_uuid] || []) , cell]
            };
        }, {});
        parentCells.forEach((parent) => {
            parent.children = childMap[String(parent.id)] || [];
        });


        this.cells.splice(
            0,
            this.cells.length,
            ...parentCells
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
