import { ref, computed } from 'vue';
import { defineStore } from 'pinia';

export const useContextStore = defineStore('beakerContext', () => {
  // const baseUrlRef = ref<string>();

  // const confUrl = computed<string>(() => {
  //   return `${baseUrlRef.value}/config`;
  // });
  // // const confUrl = URLExt.join(baseUrl, '/config')

  // // return { count, doubleCount, increment }
  // async function init(baseUrl: string) {
  //   baseUrlRef.value = baseUrl;
  //   const configResponse = await fetch(confUrl.value);
  //   const config = await configResponse.json();



  // }
  return {
    // baseUrl: baseUrlRef,
    // init,

  }
})
