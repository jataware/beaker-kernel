import { SessionContext } from '@jupyterlab/apputils';
import { ServerConnection } from '@jupyterlab/services/lib/serverconnection';
import {IKernelConnection} from '@jupyterlab/services/lib/kernel/kernel'
import { ServiceManager } from '@jupyterlab/services';
import * as messages from '@jupyterlab/services/lib/kernel/messages';
import { JSONObject } from '@lumino/coreutils';
import { v4 as uuidv4 } from 'uuid';
import fetch from 'node-fetch';
import { Slot } from '@lumino/signaling';

import { createMessageId, IBeakerAvailableContexts, IBeakerFuture, IActiveContextInfo } from './util';
import { BeakerNotebook, IBeakerShellMessage, BeakerRawCell, BeakerCodeCell, BeakerMarkdownCell, BeakerQueryCell, IBeakerIOPubMessage } from './notebook';
import { BeakerHistory } from './history';
import { BeakerRenderer, IBeakerRendererOptions } from './render';


export interface IBeakerSessionOptions {
    settings: any;
    name: string;
    kernelName: string;
    sessionId?: string;
    rendererOptions?: IBeakerRendererOptions;
    messageHandler?: Slot<any, any>;
    context?: {
        slug: string,
        payload: any,
    }
};


/**
 * Main class for connecting to and working with a Beaker kernel.
 */
export class BeakerSession {

    constructor(options?: IBeakerSessionOptions) {
        this._sessionId = uuidv4();
        this._sessionOptions = options;
        this._serverSettings = ServerConnection.makeSettings(options.settings);
        this._services = new ServiceManager({
            serverSettings: this._serverSettings,
        });
        this._services.connectionFailure.connect((sender, args) => {console.log("CONNECTION ERROR:", sender, args)});
        this._renderer = new BeakerRenderer(options.rendererOptions);
        this._history = new BeakerHistory(this._sessionId);

        this.notebook = new BeakerNotebook();
        this._initialized = new Promise(async (resolve, reject) => {
            this._services.ready.then(async () => {
                await this.initialize(options);
                if (options.context) {
                    await this.setContext({
                        context: options.context.slug,
                        context_info: options.context.payload,
                    });
                }
            });
            resolve();
        });
    }

    /**
     * Internal initialization logic once all the services are up and ready.
     */
    private async initialize(options: IBeakerSessionOptions) {

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

        // Track all messages from kernels. The disconnect on newValue is in case the kernel connection is reused, to
        // not set up duplicate handlers.
        this._sessionContext.kernelChanged.connect((sender, {oldValue, newValue, name}) => {
            oldValue?.anyMessage.disconnect(this._sessionMessageHandler, this);
            newValue?.anyMessage.disconnect(this._sessionMessageHandler, this);
            newValue?.anyMessage.connect(this._sessionMessageHandler, this);
        });

        // Initialize the session
        await this._sessionContext.initialize();
        await this._sessionContext.ready;
        if (options.messageHandler) {
            this._messageHandler = options.messageHandler;
            this._sessionContext.iopubMessage.connect(this._messageHandler);
        }
        else {
            this._messageHandler = undefined;
        }
    }

    /**
     * Low-level method for sending a message to the Beaker kernel over the "shell" channel.
     *
     * @param messageType - The message type, as passed in `msg.header.msg_type`
     * @param content - Any JSON-encodable payload to be included with the message
     * @param messageId - (Optional) Pre-defined id for the message. One will be generated if not provided.
     */
    public sendBeakerMessage(
        messageType: string,
        content: JSONObject,
        messageId: string = null
    ): IBeakerFuture {
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

        const future: IBeakerFuture = this.kernel.sendShellMessage(
            msg,
            true,
            true
        );
        future.msgId = messageId;
        return future;
    }

    /**
     * Handler for session-specific messages from the Beaker kernel.
     * This handler will be evoked for all IOPub messages, but should ignore all messages that are not session-specific.
     *
     * @param _sessionContext - The session Context related to the incoming message
     * @param msg - The incoming IOPub message
     */
    private _sessionMessageHandler(_kernel: IKernelConnection, {msg, direction}) {
        if (msg.header.msg_type === "context_setup_response" || msg.header.msg_type === "context_info_response") {
            if (msg.header.msg_type === "context_setup_response") {
                this._sessionInfo = msg.content;
            }
            else if (msg.header.msg_type === "context_info_response") {
                this._sessionInfo = msg.content.info;
            }
            this.notebook.setSubkernelInfo(this._sessionInfo);
        }
        else if (msg.header.msg_type === "kernel_info_reply") {
            this._kernelInfo = msg.content;
        }
    }

    /**
     * Returns a promise, that once resolved provides all Beaker contexts available in the session.
     */
    public async availableContexts(): Promise<IBeakerAvailableContexts> {
        return new Promise(async (resolve) => {
            const url = `${this._serverSettings.baseUrl}contexts`;
            const response = await fetch(`${this._serverSettings.baseUrl}contexts`);
            const data = await response.json();
            resolve(data);
        });
    }

    /**
     * Returns a promise that once resolved provides detailed information about the active context.
     */
    public async activeContext(): Promise<IActiveContextInfo> {
        return new Promise(async (resolve, reject)  => {
            await this.sessionReady;
            const future = this.sendBeakerMessage(
                "context_info_request",
                {}
            );
            future.onIOPub = async (msg: any) => {
                if (msg.header.msg_type === "context_info_response") {
                    resolve({
                        ...msg.content,
                        kernelInfo: await this.kernel.info,
                    });
                }
            }
            await future.done;
            reject({});
        });
    }

    public async setContext(contextPayload: any): Promise<IActiveContextInfo> {
        return new Promise(async (resolve, reject) => {
            const setupResult = this.sendBeakerMessage(
                "context_setup_request",
                contextPayload
            );
            await setupResult.done;
            const contextInfo = setupResult.msg.content as IActiveContextInfo;
            const kernelInfo = await this.kernel.requestKernelInfo();

            resolve({
                ...contextInfo,
                kernelInfo: kernelInfo.content,
            })
        });
    }

    /**
     * Executes a Beaker Action, handling all of the message
     *
     * The usual IBeakerFuture response handlers can be applied to the returned future to do act upon the responses.
     *
     * @param actionName - Name of the action to execute
     * @param payload - Payload to pass along with the action
     * @param messageId - (Optional) Id for request message. If not provided, will be generated automatically.
     * @returns - A future
     */
    public executeAction(actionName: string, payload: JSONObject, messageId: string = null): IBeakerFuture {
        const requestType = `${actionName}_request`;
        const responseType = `${actionName}_response`;
        const messageFuture: IBeakerFuture = this.sendBeakerMessage(
            requestType,
            payload,
            messageId,
        )
        const responseHandler = async (msg: IBeakerIOPubMessage): Promise<boolean> => {
            if (msg.header.msg_type === responseType && messageFuture.onResponse) {
                await messageFuture.onResponse(msg);
            }
            else if (msg.header.msg_type === "code_cell") {
                const nb = this.notebook;
                const codeCell = new BeakerCodeCell({
                    cell_type: "code",
                    source: msg.content.code,
                    metadata: {},
                    outputs: [],
                });
                nb.addCell(codeCell);
            }
            return true;
        }
        messageFuture.registerMessageHook(responseHandler)
        return messageFuture;
    }

    /**
     *
     * @param source - The `code` contents of the cell.
     * @param metadata - (Optional) Any metadata to be associated with the cell.
     * @param outputs - (Optional) Any outputs that should be included/displayed.
     * @returns - A reference to the generated cell
     */
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

    /**
     * Convenience method for adding a MarkdownCell to the notebook
     *
     * @param source - The raw markdown encoded text that should be rendered upon execute
     * @param metadata - (Optional) Any metadata to be associated with the cell.
     * @returns - A reference to the generated cell
     */
    public addMarkdownCell(source: string, metadata={}) {
        const cell = new BeakerMarkdownCell({
            cell_type: "markdown",
            source,
            metadata,
        });
        this.notebook.addCell(cell);
        return cell;
    }

    /**
     * Convenience method for adding a RawCell to the notebook
     *
     * @param source - The raw contents to be included in the raw cell.
     * @param metadata - (Optional) Any metadata to be associated with the cell.
     * @returns - A reference to the generated cell
     */
    public addRawCell(source:string, metadata={}) {
        const cell = new BeakerRawCell({
            cell_type: "raw",
            source,
            metadata,
        });
        this.notebook.addCell(cell);
        return cell;
    }

    /**
     * Convenience method for adding a QueryCell to the notebook
     *
     * @param source - The contents of the query for the LLM as a plain string
     * @param metadata - (Optional) Any metadata to be associated with the cell.
     * @returns - A reference to the generated cell
     */
    public addQueryCell(source: string, metadata={}) {
        const cell = new BeakerQueryCell({
            cell_type: "query",
            source,
            metadata,
        });
        this.notebook.addCell(cell);
        return cell;
    };

    // public toJSON(): string {
    //     return JSON.stringify({
    //         notebook: this.notebook?.toJSON()
    //     });
    // }

    // public fromJSON(): BeakerSession {
    //     // TODO
    //     return new BeakerSession();
    // }

    /**
     * Populates the sessions notebook with the provided notebook json
     *
     * @param notebookJSONObject - The json representation of a notebook, as found inside an .ipynb file
     */
    public loadNotebook(notebookJSONObject: object) {
        this.notebook.loadFromIPynb(notebookJSONObject);
    }

    /**
     * Completely resets the session, clearing the notebook and history, and restarting the fresh kernel so it is in a fresh state.
     */
    public reset() {
        // Remove cells via splice to ensure reactivity
        this.notebook.cells.splice(0, this.notebook.cells.length);
        this._history.clear();
        this._sessionContext.restartKernel();
    }

    /**
     * A promise that resolves once everything the session requires are also ready.
     */
    get sessionReady(): Promise<void> {
        return new Promise(async (resolve) => {
            await this._services.ready;
            await this._sessionContext.ready;
            await this._initialized;
            resolve();
        })
    }

    /**
     * A reference to the underlying Jupyter SessionContext for this Beaker Session.
     */
    get session(): SessionContext {
        return this._sessionContext;
    }

    /**
     * A reference to the Jupyter KernelConnection object for this session.
     */
    get kernel(): IKernelConnection {
        return this._sessionContext?.session?.kernel;
    }

    get kernelInfo() {
        return this._kernelInfo;
    }

    /**
     * A reference to the Jupyter ServiceManager which contains all of the services for this session.
     */
    get services(): ServiceManager {
        return this._services;
    }

    get renderer(): BeakerRenderer {
        return this._renderer;
    }

    get sessionId(): string {
        return this._sessionContext.path;
    }

    private _initialized: Promise<void>;
    private _sessionId: string;
    private _sessionOptions: IBeakerSessionOptions;
    private _services: ServiceManager;
    private _serverSettings: ServerConnection.ISettings;
    private _sessionContext: SessionContext;
    private _messageHandler: Slot<any, any>; // TODO: fix any typing here
    private _history: BeakerHistory;
    private _sessionInfo: any;
    private _renderer: BeakerRenderer;
    private _kernelInfo: any;

    public notebook: BeakerNotebook;

}
