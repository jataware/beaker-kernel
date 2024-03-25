<template>
    <BeakerNotebook
      :connectionStatus="connectionStatus"
      :debugLogs="debugLogs"
      :rawMessages="rawMessages"
      :previewData="previewData"
      @clear-preview="previewData = undefined"
    />
    <Toast position="bottom-right" />
</template>

<script setup lang="ts">
import { defineProps, reactive, ref, onBeforeMount, provide } from 'vue';
import { BeakerSession, JupyterMimeRenderer  } from 'beaker-kernel';
import BeakerNotebook from './components/BeakerNotebook.vue';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';
import { DecapodeRenderer, JSONRenderer, LatexRenderer, wrapJupyterRenderer } from './renderers';
import { standardRendererFactories } from '@jupyterlab/rendermime';


const toast = useToast();

// Let's only use severity=success|warning|danger(=error) for now
const showToast = ({title, detail, life=3000, severity='success', position='bottom-right'}) => {
    toast.add({
      summary: title,
      detail,
      life,
      // for options, seee https://primevue.org/toast/
      severity,
      position
    });
};

const props = defineProps([
  "config"
]);

const renderers = [
  ...standardRendererFactories.map((factory) => new JupyterMimeRenderer(factory)).map(wrapJupyterRenderer),
  JSONRenderer,
  LatexRenderer,
  DecapodeRenderer,
]

const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.has("session") ? urlParams.get("session") : "dev_session";

if (sessionId !== "dev_session") {
  window.addEventListener("beforeunload", (evt) => {
    evt.returnValue = true;
    evt.preventDefault();
  });
}

const rawSession = new BeakerSession(
  {
    settings: props.config,
    name: "MyKernel",
    kernelName: "beaker_kernel",
    sessionId: sessionId,
    rendererOptions: {
      renderers
    }
  }
);

const connectionStatus = ref('connecting');
const debugLogs = ref<object[]>([]);
const rawMessages = ref<object[]>([])
const previewData = ref<any>();

provide('show_toast', showToast);

rawSession.sessionReady.then(() => {

    rawSession.session.iopubMessage.connect((session, msg) => {

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

onBeforeMount(() => {
  document.title = "Beaker Development Interface"
});

const beakerSession = reactive(rawSession);
provide('session', beakerSession);


</script>

<style lang="scss">
#app {
  margin: 0;
  padding: 0;
  overflow: hidden;
}
</style>
