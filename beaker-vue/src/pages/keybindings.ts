import { capitalize } from "vue";
import * as f from "vue/jsx-runtime"
import * as j from "@vue/runtime-core"
import * as k from "@vue/runtime-dom"
import { withModifiers, withKeys } from "vue";

console.log('f', f);
console.log('j', j);
console.log('k', k);

const execute = (...a) => {
  console.log("I'm executing");
}

const advanceCell = () => {
  console.log("Moving to next cell");
}


const mapBindings = (keyBindings) => {
  const vOnMap = {};
  Object.entries(keyBindings).forEach(([keyBindingString, action]) => {
    const [eventtype, ...modifiers] = keyBindingString.toLowerCase().split('.');
    // if (eventtype === '') {
    //   eventtype = 'period';
    // }

    // const key = 'on' + capitalize(eventtype) + modifiers.map(capitalize).join("");
    // const key = capitalize(eventtype) + modifiers.map(capitalize).join("");
    const key = eventtype + modifiers.map(capitalize).join("");
    vOnMap[key] = action;


    // if (keyMap[key] === undefined) {
    //   keyMap[key] = [
    //     {
    //       modifiers,
    //       action,
    //     }
    //   ]
    // }
    // else {
    //   // TODO: What to do if modifiers are already defined? Just have twice?
    //   keyMap[key].push(
    //     {
    //       modifiers,
    //       action,
    //     }
    //   )
    // }
  });
  return vOnMap;
};

export default mapBindings({
  "enter.ctrl.prevent": execute,
  "enter.shift.prevent": () => {execute(); advanceCell();},
})

// export const notebookKeyBindings = mapBindings({
export const notebookKeyBindings = {
  // "keydown": () => {console.log('hi')},
  "keydown.prevent": () => {console.log('ctrl')},
  "keydown.enter.ctrl.prevent": execute,
  "keydown.enter.shift.prevent": () => {execute(); advanceCell();},
}
