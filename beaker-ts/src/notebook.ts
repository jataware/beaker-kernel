import * as nbformat from '@jupyterlab/nbformat';
import { Kernel } from '@jupyterlab/services/lib/kernel';
import * as messages from '@jupyterlab/services/lib/kernel/messages';
import { JSONObject, PartialJSONValue } from '@lumino/coreutils';
import { v4 as uuidv4 } from 'uuid';

import { BeakerSession } from './session';
import { } from './util';
import { MenuSvg } from '@jupyterlab/ui-components';

export interface IBeakerHeader extends messages.IHeader {
    msg_type: any
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

export interface IBeakerFuture extends Kernel.IShellFuture {

}

export type BeakerCellStatus = messages.Status | "awaiting_input";

export type BeakerCellType = nbformat.CellType | string | 'query';

export class BeakerBaseCell implements nbformat.IBaseCell {
    // Override index type to allow methods to be defined on the class
    [key: string]: any;
    cell_type: BeakerCellType;
    metadata: Partial<nbformat.ICellMetadata>;
    source: nbformat.MultilineString;
    status: BeakerCellStatus;

    constructor() {
        this.status = "idle";
    }
}

export interface IBeakerQueryEvent extends JSONObject {
    type: "thought" | "response" | "user_question" | "user_answer" | "error";
    content: string;

};

export interface IQueryCell extends nbformat.IBaseCell {
    cell_type: 'query';
    id?: string;
    events: IBeakerQueryEvent[];
}

export class BeakerRawCell extends BeakerBaseCell implements nbformat.IRawCell {
    cell_type: 'raw';
    id?: string;
    attachments?: nbformat.IAttachments;
    metadata: Partial<nbformat.IRawCellMetadata>;

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
    cell_type: 'code';
    id?: string;
    outputs: nbformat.IOutput[];
    execution_count: nbformat.ExecutionCount;
    metadata: Partial<nbformat.ICodeCellMetadata>;

    constructor(content: nbformat.ICell) {
        super();
        Object.keys(content).forEach((key) => {this[key] = content[key] });
        if (this.id === undefined) {
            this.id = uuidv4();
        }
        if (this.execution_count === undefined) {
            this.execution_count = null;
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
                // TODO: Additional success handling?
            }
            else if (msg.content.status === "error") {
                this.outputs.push({
                    output_type: "error",
                    content: {
                        ename: msg.content.ename,
                        evalue: msg.content.evalue,
                        traceback: msg.content.traceback,
                    },
                });
            }
            else if (msg.content.status === "abort") {
                this.outputs.push({
                    output_type: "error",
                    content: {
                        ename: "Execution aborted",
                        evalue: "Execution aborted",
                        traceback: [],
                    },
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
}

export class BeakerMarkdownCell extends BeakerBaseCell implements nbformat.IMarkdownCell {
    cell_type: 'markdown';
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
    cell_type: 'query';
    id?: string;
    events: IBeakerQueryEvent[];

    _current_input_request_message: messages.IInputRequestMsg;

    constructor(content: nbformat.ICell) {
        super();
        Object.keys(content).forEach((key) => {this[key] = content[key] });
        this.events = this.events || [];
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
                // TODO: Additional success handling?
            }
            else if (msg.content.status === "error") {
                this.events.push({
                    type: "error",
                    content: msg.content.evalue,
                });
            }
            else if (msg.content.status === "abort") {
                this.events.push({
                    type: "error",
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
                renderedMarkdownLines.push(`Beaker asks: ${event.content}`);
            }
            else if (event.type === "user_answer") {
                renderedMarkdownLines.push(`The user responds: ${event.content}`);
            }
        });
        const renderedMarkdown = renderedMarkdownLines.join("\n");
        const metadata = {
            ...this.metadata,
            beaker_cell_type: "query",
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

    public toJSON() {
        return this.toMarkdownCell();
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
            metadata: {},
        }

        // Using a Proxy to get around issues with reactivity in getters/setters
        this.cells = new Proxy(this.content.cells, {});
    }

    public toJSON() {
        return JSON.stringify(this.content);
    }

    public addCell(cell: IBeakerCell | nbformat.ICell) {
        this.cells.push(cell);
    }

    public removeCell(index: number) {
        this.cells.splice(index, 1);
    }

    private content: BeakerNotebookContent;
    public cells: IBeakerCell[];
}
