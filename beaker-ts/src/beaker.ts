import { SessionContext } from '@jupyterlab/apputils';
import {
	// ServerConnection,
	KernelManager,
	KernelSpecManager,
	SessionManager
} from '@jupyterlab/services';
import { ServerConnection } from '@jupyterlab/services/lib/serverconnection';
import { Kernel, KernelConnection } from '@jupyterlab/services/lib/kernel';
import { NotebookModelFactory } from '@jupyterlab/notebook';
import {IKernelConnection} from '@jupyterlab/services/lib/kernel/kernel'
import * as messages from '@jupyterlab/services/lib/kernel/messages';
import { JSONObject } from '@lumino/coreutils';
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

// export class BeakerKernelConnection extends KernelConnection {
//   sendBeakerMessage(
//     messageType: string,
//     content: JSONObject,
//     messageId: string = null,
//     expectReply = false,
//     disposeOnDone = true
//   ): IBeakerFuture {


    // const msg: IBeakerMessage = {
    //         buffers: null,
    //         content: {
    //             "foo": "bar"
    //         },
    //         channel: "shell",

    //         /**
    //          * The message header.
    //          */
    //         header: {
    //             date: "foo321",
    //             /**
    //              * Message id, typically UUID, must be unique per message
    //              */
    //             msg_id: "foo123",
    //             /**
    //              * Message type
    //              */
    //             msg_type: "llm_query",
    //             /**
    //              * Session id, typically UUID, should be unique per session.
    //              */
    //             session: "foo",
    //             /**
    //              * The user sending the message
    //              */
    //             username: "none",
    //             /**
    //              * The message protocol version, should be 5.1, 5.2, 5.3, etc.
    //              */
    //             version: "5.3",
    //         },
    //         /**
    //          * Metadata associated with the message.
    //          */
    //         metadata: {},
    //         /**
    //          * The parent message
    //          */
    //         parent_header: null,
    //     }

    // const future = this.sendShellMessage(
    //    msg,
    //    true,
    //    true
    // );
    // return future;
//   }
// }

// KernelConnection.prototype.sendBeakerMessage = BeakerKernelConnection.prototype.sendBeakerMessage;

export class BeakerSession {

    constructor(options?: {
        settings: any;
        name: string;
        kernelName: string;
    }) {
        this._serverSettings = ServerConnection.makeSettings(options.settings);
		this._kernelManager = new KernelManager({
			serverSettings: this._serverSettings
		});
		this._sessionManager = new SessionManager({
			kernelManager: this._kernelManager,
			serverSettings: this._serverSettings
		});
		this._specsManager = new KernelSpecManager({
			serverSettings: this._serverSettings
		});

        this._sessionContext = new SessionContext({
            sessionManager: this._sessionManager,
            specsManager: this._specsManager,
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
            console.log(this);
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
        console.log('future?', future);

        return future;
    }

    private _messageHandler(sessionConnection: ISessionConnection, {direction, msg}) {
        if (messages.isExecuteResultMsg(msg)) {
            console.log(msg, ` is an execution result`);
        }
        else if (messages.isStreamMsg(msg)) {
            console.log(msg, ` is a stream message`);
        }
        else if (messages.isStatusMsg(msg)) {
            console.log(msg, ` is a status message`);
        }
        else if (messages.isCommOpenMsg(msg)) {
            console.log(msg, ` is an commopen message`);
        }
        else if (messages.isErrorMsg(msg)) {
            console.log(msg, ` is an error message`);
        }
        else if (msg.channel === "iopub") {
            console.log(msg, ` is an iopub message`);
        }
        else if (msg.channel === "shell") {
            console.log(msg, ` is a shell message`);
        }
        else {
            console.log("unhandled", msg);
        }
    }

    get session(): SessionContext {
        return this._sessionContext;
    }

    get kernel(): KernelConnection {
        const kernel = this._sessionContext.session.kernel;
        return kernel;
    }

    private _serverSettings;
    private _kernelManager;
    private _sessionManager;
    private _specsManager;
    private _sessionContext;
    private _notebookModel;

}
