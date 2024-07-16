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

declare interface EventDefintion {
        eventType: string,
        eventOptions: {[key: string]: boolean},
        callback: () => any,
}

declare interface KeybindingDefinition extends ObjectDirective<HTMLElement, {[key: string]: () => any}> {
    parseEventDefinitions: (binding: DirectiveBinding<{[key: string]: () => any}>) => EventDefintion[],
}

export const vKeybindings: KeybindingDefinition = {
    parseEventDefinitions(binding) {
        const definitions = Object.entries(binding.value).map(([bindingDef, action]) => {
            const [eventType, key, ...modifiers] = bindingDef.toLowerCase().split('.');
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
