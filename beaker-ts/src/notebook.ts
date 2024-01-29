import * as nbformat from '@jupyterlab/nbformat';
import { Kernel } from '@jupyterlab/services/lib/kernel';
import * as messages from '@jupyterlab/services/lib/kernel/messages';
import { JSONObject, PartialJSONValue } from '@lumino/coreutils';
import { v4 as uuidv4 } from 'uuid';

import { BeakerSession } from './session';
import { } from './util';

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

export type BeakerCellType = nbformat.CellType | string | 'query' ;

export class BeakerBaseCell implements nbformat.IBaseCell {
    // Override index type to allow methods to be defined on the class
    [key: string]: any;
    cell_type: BeakerCellType;
    metadata: Partial<nbformat.ICellMetadata>;
    source: nbformat.MultilineString;
}

export interface IQueryCell extends nbformat.IBaseCell {
    cell_type: 'query';
    id?: string;
    thoughts: string[];
    debug?: string[];
    response: nbformat.MultilineString;

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
            if (msg_type === "execute_result") {
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
    thoughts: string[];
    debug?: string[];
    response: nbformat.MultilineString;

    constructor(content: nbformat.ICell) {
        super();
        Object.keys(content).forEach((key) => {this[key] = content[key] });
        this.thoughts = this.thoughts || [];
        this.debug = this.debug || [];
        this.response = this.response || "";
        if (this.id === undefined) {
            this.id = uuidv4();
        }
    }

    public execute(session: BeakerSession): IBeakerFuture | null {
        const handleIOPub = (msg: IBeakerIOPubMessage): void => {
            const msg_type = msg.header.msg_type;
            const content = msg.content;
            if (msg_type === "status") {
                return;
            }
            if (msg_type === "llm_thought") {
                this.thoughts.push(content.thought);
            }
            else if (msg_type === "llm_response" && content.name === "response_text") {
                this.response = content.text;
            }
        };

        const future = session.sendBeakerMessage(
            "llm_request",
            {
                request: this.source
            }
        );
        future.onIOPub = handleIOPub;
        return future;
    };

    public toMarkdownCell() {
        const renderedMarkdownLines = [`# ${this.source}\n`];
        this.thoughts.forEach((thought) => renderedMarkdownLines.push(`> Thought: ${thought}\n> `));
        renderedMarkdownLines.push(`\n`)
        renderedMarkdownLines.push(`**${this.response}**`)
        const renderedMarkdown = renderedMarkdownLines.join("\n");
        const metadata = {
            ...this.metadata,
            beaker_cell_type: "query",
            beaker_thoughts: this.thoughts,
            beaker_debug: this.debug,  // TODO: Do we actually want to store the debug information?
            beaker_response: this.response,
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
