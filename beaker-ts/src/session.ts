import { SessionContext } from '@jupyterlab/apputils';
import { ServerConnection } from '@jupyterlab/services/lib/serverconnection';
import {IKernelConnection} from '@jupyterlab/services/lib/kernel/kernel'
import { ServiceManager } from '@jupyterlab/services';
import * as messages from '@jupyterlab/services/lib/kernel/messages';
import { JSONObject } from '@lumino/coreutils';
import { v4 as uuidv4 } from 'uuid';
import { ISessionConnection } from '@jupyterlab/services/lib/session/session';
import fetch from 'node-fetch';
import { Slot } from '@lumino/signaling';

import { createMessageId, IBeakerAvailableContexts, IActiveContextInfo } from './util';
import { BeakerNotebook, IBeakerShellMessage, BeakerRawCell, BeakerCodeCell, BeakerMarkdownCell, BeakerQueryCell, IBeakerIOPubMessage, IBeakerFuture } from './notebook';
import { BeakerHistory } from './history';

export interface IBeakerSessionOptions {
    settings: any;
    name: string;
    kernelName: string;
    sessionId?: string;
    messageHandler?: Function;
};

export class BeakerSession {

    constructor(options?: IBeakerSessionOptions) {
        this._sessionId = uuidv4();
        this._sessionOptions = options;
        this._serverSettings = ServerConnection.makeSettings(options.settings);
        this._services = new ServiceManager({
            serverSettings: this._serverSettings,
        });
        this._history = new BeakerHistory(this._sessionId);

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

    public sendBeakerMessage(
        messageType: string,
        content: JSONObject,
        messageId: string = null
    ) {
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

    public async availableContexts(): Promise<IBeakerAvailableContexts> {
        return new Promise(async (resolve) => {
            const url = `${this._serverSettings.baseUrl}contexts`;
            const response = await fetch(`${this._serverSettings.baseUrl}contexts`);
            const data = await response.json();
            resolve(data);
        });
    }

    public async activeContext(): Promise<IActiveContextInfo> {
        return new Promise(async (resolve, reject)  => {
            await this.sessionReady;
            const future = this.sendBeakerMessage(
                "context_info_request",
                {}
            );
            future.onIOPub = (msg: any) => {
                if (msg.header.msg_type === "context_info_response") {
                    resolve(msg.content);
                }
            }
            await future.done;
            reject({});
        });
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

    public reset(fullReset: boolean = false) {
        // Remove cells via splice.
        this.notebook.cells.splice(0, this.notebook.cells.length);
        if (fullReset) {
            this._sessionContext.dispose();
            this.initialize(this._sessionOptions);
        }
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

    get kernel(): IKernelConnection {
        return this._sessionContext?.session?.kernel;
    }

    get services(): ServiceManager {
        return this._services;
    }

    private _sessionId: string;
    private _sessionOptions: IBeakerSessionOptions;
    private _services: ServiceManager;
    private _serverSettings: ServerConnection.ISettings;
    private _sessionContext: SessionContext;
    private _messageHandler: Slot<any, any>; // TODO: fix any typing here
    private _history: BeakerHistory;

    public notebook: BeakerNotebook;

}
