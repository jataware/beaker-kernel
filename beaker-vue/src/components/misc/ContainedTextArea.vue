<template>
  <Textarea
      @keyup="checkSize"
      @keydown.enter.exact.prevent="emit('submit')"
      @keydown.escape.prevent.stop="$event.target.blur()"
      autoResize
      rows="1"
      :class="{'scroll-input': allowScroll}"
      class="resizeable-textarea"
  />
</template>

<script setup>
import { defineProps, defineEmits, ref, nextTick, inject } from "vue";
import Textarea from 'primevue/textarea';

const props = defineProps({
  maxHeight: {
    type: [Number, String],
    default: '12rem'
  }
});

const emit = defineEmits([
   'submit'
]);

/**
 * Only add scrollbar when reached a specific height- else overflow-y will
 * not work properly with primevue:Textarea's autosize in combination
 * with a max-height property.
 * Somewhat hacky, but gets the job done until we have a better option.
 **/
const checkSize = (event) => {
  allowScroll.value = event.target.offsetHeight >= 180;
}

const allowScroll = ref(false);
</script>

<style lang="scss">

.resizeable-textarea {
    min-height: 3rem;

    &::placeholder {
        color: var(--gray-400);
    }
}

.scroll-input {
  overflow-y: auto !important; // Override inline style from primevue
  max-height: v-bind('props.maxHeight');
}
</style>
