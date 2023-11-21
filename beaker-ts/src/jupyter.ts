// import { SessionContext } from '@jupyterlab/apputils';
// import {
// 	ServerConnection,
// 	KernelManager,
// 	KernelSpecManager,
// 	SessionManager
// } from '@jupyterlab/services';
// import { CodeMirrorMimeTypeService } from '@jupyterlab/codemirror';
// import {
// 	standardRendererFactories as initialFactories,
// 	RenderMimeRegistry
// } from '@jupyterlab/rendermime';
// import { JSONObject } from '@lumino/coreutils';
// import * as messages from '@jupyterlab/services/lib/kernel/messages';
// import * as kernel from '@jupyterlab/services/lib/kernel/kernel';
// import { KernelConnection as JupyterKernelConnection } from '@jupyterlab/services/lib/kernel';
// import API from '@/api/api';

// declare module '@jupyterlab/services/lib/kernel/messages' {
// 	export function createMessage(options: JSONObject): JupyterMessage;
// }

// declare module '@jupyterlab/services/lib/kernel/kernel' {
// 	interface IKernelConnection {
// 		sendJupyterMessage<T extends JupyterMessage>(msg: T): void;
// 		// sendShellMessage<T extends JupyterMessage>(msg: T): void;
// 	}
// }
// declare module '@jupyterlab/services' {
// 	class KernelConnection extends JupyterKernelConnection implements kernel.IKernelConnection {
// 		sendJupyterMessage<T extends JupyterMessage>(msg: T): void;
// 		// sendShellMessage<T extends JupyterMessage>(msg: T): void;
// 	}
// }
// JupyterKernelConnection.prototype.sendJupyterMessage = function (msg) {
// 	return this.sendShellMessage(msg);
// };





// export type JupyterMessageType =
// 	| 'code_cell'
// 	| 'save_dataset_request'
// 	| 'save_dataset_response'
// 	| 'download_request'
// 	| 'download_response'
// 	| 'dataset'
// 	| 'model_preview'
// 	| 'visualization'
// 	| 'llm_request'
// 	| 'llm_response'
// 	| messages.MessageType;

// export interface IJupyterHeader<T extends JupyterMessageType> {
// 	/**
// 	 * ISO 8601 timestamp for when the message is created
// 	 */
// 	date: string;
// 	/**
// 	 * Message id, typically UUID, must be unique per message
// 	 */
// 	msg_id: string;
// 	/**
// 	 * Message type
// 	 */
// 	msg_type: T;
// 	/**
// 	 * Session id, typically UUID, should be unique per session.
// 	 */
// 	session: string;
// 	/**
// 	 * The user sending the message
// 	 */
// 	username: string;
// 	/**
// 	 * The message protocol version, should be 5.1, 5.2, 5.3, etc.
// 	 */
// 	version: string;
// }

// export interface IJupyterMessageContent {
// 	request?: string;
// 	response?: string;
// 	text?: string;
// 	code?: string;
// 	language?: string;
// 	data?: any;
// }

// export interface IJupyterMessage<T extends JupyterMessageType = JupyterMessageType> {
// 	/**
// 	 * An optional list of binary buffers.
// 	 */
// 	buffers?: (ArrayBuffer | ArrayBufferView)[];
// 	/**
// 	 * The channel on which the message is transmitted.
// 	 */
// 	channel: messages.Channel;
// 	/**
// 	 * The content of the message.
// 	 */
// 	content: IJupyterMessageContent | any;
// 	/**
// 	 * The message header.
// 	 */
// 	header: IJupyterHeader<T>;
// 	/**
// 	 * Metadata associated with the message.
// 	 */
// 	metadata: JSONObject;
// 	/**
// 	 * The parent message
// 	 */
// 	parent_header: messages.IHeader | any;
// }

// export declare type JupyterMessage = IJupyterMessage | messages.Message;

// // TODO: These settings should be pulled from the environment variables or appropriate config setup.
// let serverSettings;
// // export const getServerSettings = () => serverSettings;
// let kernelManager;
// // export const getKernelManager = () => kernelManager;

// let specsManager;
// // export const getSpecsManager = () => specsManager;

// let sessionManager;
// // export const getSessionManager = () => sessionManager;

// // export const mimeService = new CodeMirrorMimeTypeService();

// // export const renderMime = new RenderMimeRegistry({ initialFactories });
// let initialized = false;

// export const newSession = async (kernelName: string, name: string) => {
// 	if (!initialized) {
// 		// const settingsResponse = await API.get('/tgpt/configuration');
// 		// const settings = settingsResponse.data;
// 		const settings = {

// 		};
// 		serverSettings = ServerConnection.makeSettings(settings);
// 		kernelManager = new KernelManager({
// 			serverSettings
// 		});
// 		sessionManager = new SessionManager({
// 			kernelManager,
// 			serverSettings
// 		});
// 		specsManager = new KernelSpecManager({
// 			serverSettings
// 		});
// 		initialized = true;
// 	}

// 	const sessionContext = new SessionContext({
// 		sessionManager,
// 		specsManager,
// 		name,
// 		kernelPreference: {
// 			name: kernelName
// 		}
// 	});

// 	sessionContext.initialize();
// 	return sessionContext;
// };

// export interface IMessageHistory {
// 	message: string;
// 	messageType: string;
// }
