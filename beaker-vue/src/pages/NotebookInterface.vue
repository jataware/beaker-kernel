<template>
  <div id="app">
    <div id="notebook-container">
      <BeakerSession
        v-bind="props"
      >
        <BeakerHeader
          :connectionStatus="connectionStatus"
        />
          <!-- :toggleDarkMode="toggleDarkMode"
          :loading="!activeContext?.slug"
          :kernel="selectedKernel"
          @select-kernel="toggleContextSelection" -->
        <BeakerNotebook
          class="notebook"
          :connectionStatus="connectionStatus"
        />
      </BeakerSession>
    </div>
    <Toast position="bottom-right" />
  </div>
</template>

<script setup lang="ts">
import { defineProps, reactive, ref, onBeforeMount, provide } from 'vue';
import { JupyterMimeRenderer  } from 'beaker-kernel';
import BeakerNotebook from '@/components/notebook/BeakerNotebook.vue';
import BeakerSession from '@/components/session/BeakerSession.vue';
import BeakerHeader from '@/components/dev-interface/BeakerHeader.vue';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';
import { DecapodeRenderer, JSONRenderer, LatexRenderer, wrapJupyterRenderer } from '../renderers';
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
  "connectionSettings",
  "sessionName",
  "sessionId",
  "defaultKernel",
  "renderers",

]);


const renderers = [
  ...standardRendererFactories.map((factory) => new JupyterMimeRenderer(factory)).map(wrapJupyterRenderer),
  JSONRenderer,
  LatexRenderer,
  DecapodeRenderer,
]

const connectionStatus = ref('connecting');

// rawSession.sessionReady.then(() => {

//     rawSession.session.iopubMessage.connect((session, msg) => {

//         if (msg.header.msg_type === 'status') {
//           setTimeout(() => {
//             const newStatus = msg?.content?.execution_state || 'connecting';
//             connectionStatus.value = newStatus == 'idle' ? 'connected' : newStatus;
//           }, 1000);
//         } else if (msg.header.msg_type === "preview") {
//           previewData.value = msg.content;
//         } else if (msg.header.msg_type === "debug_event") {
//             debugLogs.value.push({
//               type: msg.content.event,
//               body: msg.content.body,
//               timestamp: msg.header.date,
//             });
//         }

//     });
//     rawSession.session.session.anyMessage.connect((_: unknown, {msg, direction}) => {
//       rawMessages.value.push({
//         type: direction,
//         body: msg,
//         timestamp: msg.header.date,
//       });
//     });

// });

onBeforeMount(() => {
  document.title = "Beaker Development Interface"
});

// const beakerSession = reactive(rawSession);

// provide('session', beakerSession);
provide('show_toast', showToast);

</script>

<style lang="scss">
#app {
  margin: 0;
  padding: 0;
  overflow: hidden;
  background-color: var(--surface-b);
}

#notebook-container {
  display: flex;
  flex: 1;
  flex-direction: column;
  height: calc(100vh - 8px);
  margin-top: 4px;
  margin-bottom: 4px;
  box-shadow: 2px 2px 8px 4px var(--gray-700);
  margin-left: 30%;
  margin-right: 30%;
}
</style>
