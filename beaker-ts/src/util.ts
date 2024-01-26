import { v4 as uuidv4 } from 'uuid';
import { JSONObject, PartialJSONValue } from '@lumino/coreutils';


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
