import { withModifiers, withKeys, ObjectDirective, DirectiveBinding } from "vue";

const modifierKeys = [
  "ctrl",
  "alt",
  "shift",
  "meta",
];

const eventModifiersValues = [
    "passive",
    "once",
    "capture",
];

const checkInEditor = (event: Event): boolean => {
    let target: HTMLElement = (event.target as HTMLElement);
    const docElement = (event.target as HTMLElement).ownerDocument.documentElement;
    const inputTags = ['INPUT', 'TEXTAREA', 'SELECT'];
    const inputRoles = ['textbox', 'searchbox'];
    while (target !== null && target !== docElement) {
        if (inputTags.includes(target.tagName)) {
            return true;
        }

        const contentEditable = target.getAttribute('contenteditable');
        if (contentEditable?.toLowerCase() === 'true' || contentEditable === '') {
            return true;
        }

        if (target.hasAttribute('tabindex') && target.hasAttribute('role')) {
            const role = target.getAttribute('role');
            if (inputRoles.includes(role)) {
                return true;
            }
        }
        target = target.parentElement;
    }
    return false;
}

const checkInCell = (event: Event): boolean => {
    let target: HTMLElement = (event.target as HTMLElement);
    const docElement = (event.target as HTMLElement).ownerDocument.documentElement;
    const BeakerCellClass = 'beaker-cell';
    while (target !== null && target !== docElement) {
        if (target.classList.contains(BeakerCellClass)) {
            return true;
        }
        target = target.parentElement;
    }
    return false;
}

const selected = (event: Event): boolean => {
    let target: HTMLElement = (event.target as HTMLElement);
    const docElement = (event.target as HTMLElement).ownerDocument.documentElement;
    const BeakerCellClass = 'beaker-cell';
    while (target !== null && target !== docElement) {
        if (target.classList.contains(BeakerCellClass) && target.classList.contains("selected")) {
            return true;
        }
        target = target.parentElement;
    }
    return false;
}



const beakerModifiersMappings: {[key: string]: (event: Event) => boolean} = {
    'in-editor': checkInEditor,
    'in-cell': checkInCell,
    'selected': selected,
}

function withBeakerModifiers(fn: EventCallback, modifiers: string[]): EventCallback {
    return (event, ...args) => {
        for (let modifier of modifiers) {
            let negated = false;
            if (modifier.startsWith('!')) {
                negated = true;
                modifier = modifier.slice(1);
            }
            const guardFunction = beakerModifiersMappings[modifier];
            if (guardFunction === undefined) {
                continue;
            }
            const conditionMatches = guardFunction(event);
            const blockExecution = negated ? conditionMatches : !conditionMatches;
            if (blockExecution) {
                return;
            }
        }
        return fn(event);
    }
}

export declare type EventCallback = (evt: Event, ...args: any[]) => any;

export declare interface EventDefintion {
        eventType: string,
        eventOptions: {[key: string]: boolean},
        callback: EventCallback,
}

export declare interface KeybindingDefinition extends ObjectDirective<HTMLElement, {[key: string]: EventCallback}> {
    parseEventDefinitions: (binding: DirectiveBinding<{[key: string]: EventCallback}>) => EventDefintion[],
}

export const vKeybindings: KeybindingDefinition = {
    parseEventDefinitions(binding) {
        const definitions = Object.entries(binding.value).map(([bindingDef, action]) => {
            const [eventType, key, ...modifiers] = bindingDef.toLowerCase().split('.');

            const customModifiers = modifiers.filter(
                (item) => Object.keys(beakerModifiersMappings).some(
                    (customModifier) => RegExp(`!?${customModifier}`, 'i').test(item)
                )
            );
            const keyModifiers = modifiers.filter((item) => !eventModifiersValues.includes(item));
            const eventModifiers = modifiers.filter((item) => eventModifiersValues.includes(item));
            if (eventType === undefined || key === undefined || eventType === "" || key === "") {
                console.warn(`Keybinding definition '${bindingDef}' cannot be parsed. Please ensure it is in the format of '{eventtype}.{key}(.{modifier})*'`)
            }
            let callback = action;
            if (keyModifiers.length) {
                callback = withModifiers(callback, keyModifiers);
            }

            callback = withKeys(callback, [key]);

            if (customModifiers.length) {
                callback = withBeakerModifiers(callback, customModifiers);
            }

            const eventOptions = eventModifiers.reduce((obj, val) => {obj[val] = true; return obj;}, {});

            return {
                eventType,
                eventOptions,
                callback,
            };
        });
        return definitions;
    },

    beforeMount(el, binding, vnode) {
        // Bindings
        const eventListeners = vKeybindings.parseEventDefinitions(binding);
        eventListeners.forEach((eventDefinition) => {
            const {eventType, eventOptions, callback} = eventDefinition;
            el.addEventListener(eventType, callback, eventOptions);
        });
    },
    unmounted(el: HTMLElement, binding, vnode) {
        // Cleanup
        const eventListeners = vKeybindings.parseEventDefinitions(binding);
        eventListeners.forEach((eventDefinition) => {
            const {eventType, eventOptions, callback} = eventDefinition;
            el.removeEventListener(eventType, callback, eventOptions);
        });
    },
}
