<template>
  <slot>
    <BeakerNotebook
      :connectionStatus="connectionStatus"
      :debugLogs="debugLogs"
      :rawMessages="rawMessages"
      :previewData="previewData"
      @clear-preview="previewData = undefined"
    />
  </slot>
</template>

<script setup lang="ts">
import { defineProps, reactive, ref, onBeforeMount, provide } from 'vue';
import { BeakerSession, JupyterMimeRenderer  } from 'beaker-kernel';
// import BeakerNotebook from '@/components/notebook/BeakerNotebook.vue';


const props = defineProps([
  "connectionSettings",
  "sessionName",
  "sessionId",
  "defaultKernel",
  "renderers",

]);

const rawSession = new BeakerSession(
  {
    settings: props.connectionSettings,
    name: props.sessionName,
    sessionId: props.sessionId,
    kernelName: props.defaultKernel,
    rendererOptions: {
      renderers: props.renderers || []
    }
  }
);

const connectionStatus = ref('connecting');
const debugLogs = ref<object[]>([]);
const rawMessages = ref<object[]>([])
const previewData = ref<any>();

rawSession.sessionReady.then(() => {

    rawSession.session.iopubMessage.connect((session, msg) => {
      console.log(msg);

        if (msg.header.msg_type === 'status') {
          setTimeout(() => {
            const newStatus = msg?.content?.execution_state || 'connecting';
            connectionStatus.value = newStatus == 'idle' ? 'connected' : newStatus;
          }, 1000);
        } else if (msg.header.msg_type === "preview") {
          previewData.value = msg.content;
        } else if (msg.header.msg_type === "debug_event") {
            debugLogs.value.push({
              type: msg.content.event,
              body: msg.content.body,
              timestamp: msg.header.date,
            });
        }

    });
    rawSession.session.session.anyMessage.connect((_: unknown, {msg, direction}) => {
      rawMessages.value.push({
        type: direction,
        body: msg,
        timestamp: msg.header.date,
      });
    });

});

const beakerSession = reactive(rawSession);

provide('session', beakerSession);

</script>

<style lang="scss">
</style>
