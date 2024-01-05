import * as nbformat from '@jupyterlab/nbformat';
import { SessionContext } from '@jupyterlab/apputils';
import { ServerConnection } from '@jupyterlab/services/lib/serverconnection';
import { Kernel, KernelConnection } from '@jupyterlab/services/lib/kernel';
import { INotebookModel, NotebookModelFactory } from '@jupyterlab/notebook';
import {IKernelConnection} from '@jupyterlab/services/lib/kernel/kernel'
import { ServiceManager } from '@jupyterlab/services';
import * as messages from '@jupyterlab/services/lib/kernel/messages';
import { JSONObject, JSONValue, PartialJSONValue } from '@lumino/coreutils';
import { v4 as uuidv4 } from 'uuid';
import { ISessionConnection } from '@jupyterlab/services/lib/session/session';
import { MethodDeclaration, convertToObject } from 'typescript';
import { renderHTML, renderImage, renderLatex, renderMarkdown, renderSVG, renderText, RenderMimeRegistry} from '@jupyterlab/rendermime';


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

export interface IBeakerMessage extends messages.IShellMessage {
    header: IBeakerHeader;
    channel: "shell";
    content: JSONObject;
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
    function createMessage<T extends IBeakerMessage>(options: messages.IOptions<T>): T;
}

export class BeakerSession {

    constructor(options?: {
        settings: any;
        name: string;
        kernelName: string;
        sessionId?: string;
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
        this._sessionContext.initialize().then((e) => {
            this._sessionContext.ready.then(() => {
                this._sessionContext.session.anyMessage.connect(this._messageHandler);
            });
        });
    }

    public sendBeakerMessage (
        messageType: string,
        content: JSONObject,
        messageId: string = null
    ) {
        if (messageId === null) {
            messageId = createMessageId(messageType);
        }
        const msg: IBeakerMessage = messages.createMessage({
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

    private _messageHandler(sessionConnection: ISessionConnection, {direction, msg}) {
        // if (messages.isExecuteResultMsg(msg)) {
        //     console.log(msg, ` is an execution result`);
        // }
        // else if (messages.isStreamMsg(msg)) {
        //     console.log(msg, ` is a stream message`);
        // }
        // else if (messages.isStatusMsg(msg)) {
        //     console.log(msg, ` is a status message`);
        // }
        // else if (messages.isCommOpenMsg(msg)) {
        //     console.log(msg, ` is an commopen message`);
        // }
        // else if (messages.isErrorMsg(msg)) {
        //     console.log(msg, ` is an error message`);
        // }
        // else if (msg.channel === "iopub") {
        //     console.log(msg, ` is an iopub message`);
        // }
        // else if (msg.channel === "shell") {
        //     console.log(msg, ` is a shell message`);
        // }
        // else {
        //     console.log("unhandled", msg);
        // }
    }

    public addCodeCell(source: string, metadata={}, outputs=[]) {
        console.log("creating new cell")
        const newCell = new BeakerCodeCell({
                cell_type: "code",
                source,
                metadata,
                outputs,
            });
        console.log("newcell1:", newCell)

        this.notebook.addCell(
            newCell
        );
    }

    public addMarkdownCell(source: string, metadata={}) {
        this.notebook.addCell(
            new BeakerMarkdownCell({
                cell_type: "markdown",
                source,
                metadata,
            })
        );
    }

    public addRawCell(source:string, metadata={}) {
        this.notebook.addCell(
            new BeakerRawCell({
                cell_type: "raw",
                source,
                metadata,
            })
        );
    }

    public toJSON(): string {
        return JSON.stringify({
            notebook: this.notebook?.toJSON()
        });
    }

    public fromJSON(): BeakerSession {

        return new BeakerSession();
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

    public notebook: BeakerNotebook;

}

export type BeakerCellType = nbformat.CellType | string | 'query' ;

export class BeakerBaseCell implements nbformat.IBaseCell {

    // constructor(content: nbformat.ICell) {
    //     console.log("Adding cell", content);
    //     console.log("before:", this);
    //     Object.keys(content).forEach((key) => {
    //         console.log("Key?: ", key);
    //         this[key] = content[key];
    //     });
    //     console.log("after:", this);
    // }

    // Override index type to allow methods to be defined on the class
    [key: string]: any;
    cell_type: BeakerCellType;
    metadata: Partial<nbformat.ICellMetadata>;
    source: nbformat.MultilineString;
}

export class BeakerRawCell extends BeakerBaseCell implements nbformat.IRawCell {
    cell_type: 'raw';
    id?: string;
    attachments?: nbformat.IAttachments;
    metadata: Partial<nbformat.IRawCellMetadata>;
}

export class BeakerCodeCell extends BeakerBaseCell implements nbformat.ICodeCell {
    cell_type: 'code';
    id?: string;
    outputs: nbformat.IOutput[];
    execution_count: number;
    metadata: Partial<nbformat.ICodeCellMetadata>;

    constructor(content: nbformat.ICell) {
        super();
        Object.keys(content).forEach((key) => {this[key] = content[key] });
    }


    public execute(session: BeakerSession): IBeakerFuture {
        const handleIOPub = (msg: messages.IIOPubMessage<messages.IOPubMessageType> | messages.IExecuteResultMsg): void => {
            const msg_type = msg.header.msg_type;
            const content = msg.content;
            if (msg_type === "execute_result") {
                const content = msg.content;
                // if (content.execution_count) {
                //     this.execution_count = content.execution_count;
                // }
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
        };
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
        console.log("I'm called!");
        return JSON.stringify(this.content);
    }

    public addCell(cell: IBeakerCell | nbformat.ICell) {
        console.log('cell1', cell);
        // if (cell.cell_type === "code") {
        //     cell = new BeakerCodeCell(cell);
        //     console.log("Generated cell:", cell);
        // }
        // console.log('cell2', cell);
        // console.log("before push", this.cells);
        this.cells.push(cell);
        // console.log("after push", this.cells);
    }

    private content: BeakerNotebookContent;
    public cells: IBeakerCell[];
}
