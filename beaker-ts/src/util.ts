import { v4 as uuidv4 } from 'uuid';
import { JSONObject } from '@lumino/coreutils';
import { KernelFutureHandler } from '@jupyterlab/services/lib/kernel/future';
import  *  as Kernel from '@jupyterlab/services/lib/kernel/kernel';

import { IBeakerShellMessage, BeakerCodeCell, IBeakerIOPubMessage, IBeakerCell } from './notebook';


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

export interface IBeakerFuture extends Kernel.IShellFuture {
    msgId?: string;
    onResponse?: (msg: any) => void | PromiseLike<void>;
}

export interface IBeakerAvailableContexts {
    [context_slug: string]: {
        languages: {
            slug: string,
            kernel: string,
        },
        defaultPayload: string,
    };
}

export interface IActiveContextInfo {
    slug: string;
    class: string;
    config: JSONObject;
    language: {
        slug: string;
        subkernel: string;
    }
}


export class BeakerCellFuture extends KernelFutureHandler<IBeakerShellMessage, IBeakerShellMessage> {
    /**
     * Construct a new KernelFutureHandler.
     */

    constructor(
        msg: IBeakerShellMessage,
        expectReply: boolean,
        disposeOnDone: boolean,
        kernel: Kernel.IKernelConnection,
        cell: BeakerCodeCell,
    ) {
        const msgId = msg.header.msg_id;
        // Ensure channel is set if created via alternate means
        if (msg.channel === undefined) {
            msg.channel = "shell";
        }
        // Clean up from kernel future list when complete.
        const disposalCallback: (() => void) = () => {
            // @ts-ignore -- Deregister future via private member for cleanup
            kernel._futures.delete(msgId);
        };
        super(disposalCallback, msg, expectReply, disposeOnDone, kernel)
        // @ts-ignore -- Register future via private member
        kernel._futures?.set(msgId, this);
        this.cell = cell;
        this.onIOPub = (msg: IBeakerIOPubMessage) => BeakerCellFutures.handleIOPub(msg, this.cell);
        this.onReply = (msg: IBeakerShellMessage) => BeakerCellFutures.handleReply(msg, this.cell);
    }


    private cell: BeakerCodeCell;
}

export namespace BeakerCellFutures {

    export const handleIOPub = (msg: IBeakerIOPubMessage, cell: IBeakerCell): void => {
        const msg_type = msg.header.msg_type;
        const content = msg.content;
        if (msg_type === "status") {
            cell.status = content.execution_state;
        }
        else if (msg_type === "execute_result") {
            cell.busy = false;
            if (content.execution_count) {
                cell.execution_count = content.execution_count;
            }
            cell.outputs.push({
                output_type: "execute_result",
                ...content
            });
        }
        else if (msg_type === "stream") {
            cell.outputs.push({
                output_type: "stream",
                ...content
            });
        }
        else if (msg_type === "display_data") {
            cell.outputs.push({
                output_type: "display_data",
                ...content
            });
        }
    };

    export const handleReply = (msg: IBeakerShellMessage, cell: IBeakerCell) => {
        cell.busy = false;
        if (msg.content.status === "ok") {
            cell.last_execution = {...cell.last_execution, status: "ok"};
            cell.execution_count = Number(msg.content.execution_count);
        }
        else if (msg.content.status === "error") {
            cell.execution_count = Number(msg.content.execution_count);
            const error_details = {
                ename: msg.content.ename,
                evalue: msg.content.evalue,
                traceback: msg.content.traceback,
            };
            cell.last_execution = {
                status: "error",
                ...error_details
            };
            cell.outputs.push({
                output_type: "error",
                ...error_details
            });
        }
        else if (msg.content.status === "abort") {
            cell.execution_count = msg.content.execution_count;
            const error_details = {
                ename: "Execution aborted",
                evalue: "Execution aborted",
                traceback: [],
            };
            cell.last_execution = {
                status: "error",
                ...error_details,
            };
            cell.outputs.push({
                output_type: "error",
                content: error_details,
            });
        }
    };

}
