import { JSONObject } from '@lumino/coreutils';
import { IBeakerShellMessage } from './notebook';
import { IBeakerFuture } from './util';
import * as messages from '@jupyterlab/services/lib/kernel/messages';
import * as nbformat from '@jupyterlab/nbformat';
import { PartialJSONObject } from '@lumino/coreutils';


declare module "@jupyterlab/services/lib/kernel" {
    export interface KernelConnection {
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
    export function createMessage<T extends IBeakerShellMessage>(options: messages.IOptions<T>): T;

}

declare module '@jupyterlab/nbformat' {
    export interface IBaseOutput extends PartialJSONObject {
        output_type: string;
        metadata?: nbformat.OutputMetadata;
    }
}

export default {};
