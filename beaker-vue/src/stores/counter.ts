import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

/** Sample demo store- unused for now. */

export const useCounterStore = defineStore('counter', () => {
  const count = ref(0)
  const doubleCount = computed(() => count.value * 2)
  function increment() {
    count.value++
  }

  return { count, doubleCount, increment }
})
