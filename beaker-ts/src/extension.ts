import { JSONObject } from '@lumino/coreutils';
import { IBeakerFuture, IBeakerShellMessage } from './notebook';
import * as messages from '@jupyterlab/services/lib/kernel/messages';


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

export default {};
