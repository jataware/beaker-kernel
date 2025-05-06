import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import urlparse from 'url-parse';


export interface ServerConfig {
  config_type: "server" | "file" | "session" | "single" | "other";
  appUrl: string;
  baseUrl: string;
  wsUrl: string;
  token: string;
  extra: {
    [key: string]: any;
  }
};

export interface UserConfig {

};

export interface AppConfig {

}

export const useConfigStore = defineStore('beakerConfig', () => {
  const baseUrlRef = ref<string>();
  const confUrl = computed(() => getPathURL("/config"));

  const serverConfig = ref<ServerConfig>();
  const userConfig = ref<UserConfig>();
  const appConfig = ref<AppConfig>();

  const serverConfigReady = computed<Promise<boolean>>(() => {
    return new Promise(async (resolve, reject) => {
      while (!serverConfig.value) {
        await new Promise(r => setTimeout(r, 30));
      }
      resolve(true);
    });
  });

  function getPathURL(path: string): string {
    return (new URL(path, baseUrlRef.value)).toString();
  }

  async function init(baseUrl?: string) {
    baseUrlRef.value = (baseUrl ? baseUrl.toString() : urlparse("/").toString());
    const configResponse = await fetch(confUrl.value);
    serverConfig.value = await configResponse.json();
    updateUserConfig();
  }

  async function updateUserConfig() {
    const configUrl = getPathURL('/config/control');
    const schemaUrl = `${configUrl}?schema`;
    const configFuture = fetch(configUrl);
    const schemaFuture = fetch(schemaUrl);
    const configResponse = await configFuture
    const schemaResponse = await schemaFuture
    const config = await configResponse.json();
    const schema = await schemaResponse.json();
    userConfig.value = {config, schema};
  }

  return {
    baseUrl: baseUrlRef,
    serverConfig,
    userConfig,
    appConfig,
    init,
    serverConfigReady,
  }
})
