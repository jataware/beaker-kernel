<template>
  <div
    class="keyboard-controller"
    ref="keyboardController"
  >
    <slot></slot>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, defineProps } from 'vue';

const props = defineProps({
  "keyBindings": {},
  "this": undefined,
});

const keyboardController = ref<HTMLDivElement>();
const keyMap = {};
const modifierKeys = [
  "ctrl",
  "alt",
  "shift",
  "meta",
]

const handleKeypress = (evt: KeyboardEvent, ...args) => {
  const keyEntries = keyMap[evt.key.toLowerCase()];
  if (keyEntries !== undefined) {
    keyEntries.forEach(({modifiers, action}) => {
      const selectedModifierKeys: string[] = modifiers.filter((item) => modifierKeys.includes(item));
      var matches;
      const exact = modifiers.includes("exact");
      if (exact) {
        matches = modifierKeys.map((item) => (evt[`${item}Key`] === selectedModifierKeys.includes(item))).reduce((l, r) => (l && r), true);
      }
      else {
        matches = selectedModifierKeys.map((item) => evt[`${item}Key`]).reduce((l, r) => (l && r), true);
      }
      if (!matches) {
        return;
      }

      action(props.this);

      if (modifiers.includes("prevent")) {
        evt.preventDefault();
      }
      if (modifiers.includes("stop")) {
        evt.stopPropagation();
      }
    });
  }
}

Object.entries(props['keyBindings']).forEach(([keyString, action]) => {
  var [key, ...modifiers] = keyString.toLowerCase().split('.');
  if (key === '') {
    key = '.';
  }
  if (keyMap[key] === undefined) {
    keyMap[key] = [
      {
        modifiers,
        action,
      }
    ]
  }
  else {
    // TODO: What to do if modifiers are already defined? Just have twice?
    keyMap[key].push(
      {
        modifiers,
        action,
      }
    )
  }
});


onMounted(() => {
  keyboardController.value?.addEventListener("keydown", handleKeypress, true);
});

</script>

<style lang="scss">
</style>
