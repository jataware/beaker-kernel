import * as nbformat from '@jupyterlab/nbformat';
import { SessionContext } from '@jupyterlab/apputils';
import { ServerConnection } from '@jupyterlab/services/lib/serverconnection';
import { Kernel, KernelConnection } from '@jupyterlab/services/lib/kernel';
import {IKernelConnection} from '@jupyterlab/services/lib/kernel/kernel'
import { ServiceManager } from '@jupyterlab/services';
import * as messages from '@jupyterlab/services/lib/kernel/messages';
import { JSONObject, PartialJSONValue } from '@lumino/coreutils';
import { v4 as uuidv4 } from 'uuid';
import { ISessionConnection } from '@jupyterlab/services/lib/session/session';


// Lower case states to match the naming in the messages.
export enum KernelState {
	unknown = 'unknown',
	starting = 'starting',
	idle = 'idle',
	busy = 'busy',
	terminating = 'terminating',
	restarting = 'restarting',
	autorestarting = 'autorestarting',
	dead = 'dead'
}


export const createMessageId = (msgType: string): string => {
	const uuid = uuidv4().replaceAll('-', '').slice(0, 16);
	return `beaker-${uuid}-${msgType}`;
};


export namespace BeakerConnection {

    interface ISettings extends ServerConnection.ISettings {
        // Beaker specific settings to go here

    }

    export function makeSettings(serverSettings?: Partial<ServerConnection.ISettings>): ISettings {
        return ServerConnection.makeSettings(serverSettings);
    }

}


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

declare module "@jupyterlab/services/lib/kernel" {
    interface KernelConnection {
        sendBeakerMessage(
            messageType: string,
            content: JSONObject,
            messageId: string,
            expectReply: boolean,
            disposeOnDone: boolean
        ): IBeakerFuture;

    }
}

declare module "@jupyterlab/services/lib/kernel/messages" {
    function createMessage<T extends IBeakerShellMessage>(options: messages.IOptions<T>): T;

}

export class BeakerSession {

    constructor(options?: {
        settings: any;
        name: string;
        kernelName: string;
        sessionId?: string;
        messageHandler?: Function; //(func: Function): void;
    }) {
        this._serverSettings = ServerConnection.makeSettings(options.settings);
        this._services = new ServiceManager({
            serverSettings: this._serverSettings,
        });

        this.notebook = new BeakerNotebook();

        this._services.ready.then(() => {
            this.initialize(options);
        })
    }

    private async initialize(options) {

        // Create (or reuse existing) a session Context
        this._sessionContext = new SessionContext({
            sessionManager: this._services.sessions,
            specsManager: this._services.kernelspecs,
            name: options.name,
            path: options.sessionId,
            kernelPreference: {
                name: options.kernelName
            }
        });

        // Initialize the session
        this._sessionContext.initialize().then(() => {
            this._sessionContext.ready.then(() => {
                if (options.messageHandler) {
                    this._messageHandler = options.messageHandler;
                }
                else {
                    this._messageHandler = this._defaultMessageHandler;
                }
                this._sessionContext.iopubMessage.connect(this._messageHandler);
            });
        });
    }

    public sendBeakerMessage (
        messageType: string,
        content: JSONObject,
        messageId: string = null
    ) {
        console.log("sendBeakerMessage");
        if (messageId === null) {
            messageId = createMessageId(messageType);
        }
        const msg: IBeakerShellMessage = messages.createMessage({
            session: this.session.session.id,
            channel: "shell",
            msgType: messageType,
            content: content,
            msgId: messageId
        });

        const future = this.kernel.sendShellMessage(
            msg,
            true,
            true
        );
        return future;
    }

    private _defaultMessageHandler(sessionConnection: ISessionConnection, {direction, msg}) {
        //noop
    }

    public addCodeCell(source: string, metadata={}, outputs=[]) {
        const cell = new BeakerCodeCell({
                cell_type: "code",
                source,
                metadata,
                outputs,
            });
        this.notebook.addCell(cell);
        return cell;
    }

    public addMarkdownCell(source: string, metadata={}) {
        const cell = new BeakerMarkdownCell({
            cell_type: "markdown",
            source,
            metadata,
        });
        this.notebook.addCell(cell);
        return cell;
    }

    public addRawCell(source:string, metadata={}) {
        const cell = new BeakerRawCell({
            cell_type: "raw",
            source,
            metadata,
        });
        this.notebook.addCell(cell);
        return cell;
    }

    public addQueryCell(source: string, metadata={}) {
        const cell = new BeakerQueryCell({
            cell_type: "query",
            source,
            metadata,
        });
        this.notebook.addCell(cell);
        return cell;
    };

    public toJSON(): string {
        return JSON.stringify({
            notebook: this.notebook?.toJSON()
        });
    }

    public fromJSON(): BeakerSession {
        // TODO
        return new BeakerSession();
    }

    get sessionReady(): Promise<void> {
        return new Promise(async (resolve) => {
            await this._services.ready;
            await this._sessionContext.ready;
            resolve();
        })
    }

    get session(): SessionContext {
        return this._sessionContext;
    }

    get kernel(): KernelConnection {
        const kernel = this._sessionContext?.session?.kernel;
        return kernel;
    }

    get services(): ServiceManager {
        return this._services;
    }

    private _services: ServiceManager;
    private _serverSettings;
    private _sessionContext;
    private _messageHandler: Function;

    public notebook: BeakerNotebook;

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
        return new BeakerMarkdownCell(
            {
                cell_type: "markdown",
                id: this.id,
                source: renderedMarkdown,
                metadata: this.metadata,
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
