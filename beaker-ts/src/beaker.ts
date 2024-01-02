import { SessionContext } from '@jupyterlab/apputils';
import { ServerConnection } from '@jupyterlab/services/lib/serverconnection';
import { Kernel, KernelConnection } from '@jupyterlab/services/lib/kernel';
import { INotebookModel, NotebookModelFactory } from '@jupyterlab/notebook';
import {IKernelConnection} from '@jupyterlab/services/lib/kernel/kernel'
import { ServiceManager } from '@jupyterlab/services';
import * as messages from '@jupyterlab/services/lib/kernel/messages';
import { JSONObject } from '@lumino/coreutils';
import { v4 as uuidv4 } from 'uuid';
import { ISessionConnection } from '@jupyterlab/services/lib/session/session';
import { ISharedNotebook } from '@jupyter/ydoc';

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
    }) {
        this._serverSettings = ServerConnection.makeSettings(options.settings);
        this._services = new ServiceManager({
            serverSettings: this._serverSettings,

        });
        void this._services.ready.then(() => {
            // Set up thing depending on services here
            this._sessionContext = new SessionContext({
                sessionManager: this._services.sessions,
                specsManager: this._services.kernelspecs,
                name: options.name,
                kernelPreference: {
                    name: options.kernelName
                }
            });

            this._notebookModel = new NotebookModelFactory({
                collaborative: false,
                disableDocumentWideUndoRedo: false,
            }).createNew({});

            // Initialize the session
            this.session.initialize();
            this.session.ready.then(() => {
                this.session.session.anyMessage.connect(this._messageHandler);
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
        this.notebook.addCell({
            cell_type: "code",
            source,
            metadata,
            outputs,
        });
    }

    public addMarkdownCell(source: string, metadata={}) {
        this.notebook.addCell({
            cell_type: "markdown",
            source,
            metadata,
        });

    }

    public addRawCell(source:string, metadata={}) {
        this.notebook.addCell({
            cell_type: "raw",
            source,
            metadata,
        })

    }

    public toJSON(): string {
        return JSON.stringify({
            notebook: this._notebookModel?.toJSON()
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

    get notebook(): ISharedNotebook {
        return this._notebookModel?.sharedModel;
    }

    get services(): ServiceManager {
        return this._services;
    }

    private _services: ServiceManager;
    private _serverSettings;
    private _sessionContext;
    private _notebookModel;

}
