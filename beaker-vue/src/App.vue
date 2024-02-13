<template>
    <BeakerNotebook
      :session="beakerSession"
      :connectionStatus="connectionStatus"
      />
</template>

<script setup lang="ts">
import { reactive, ref, onBeforeMount, provide } from 'vue';
import { BeakerSession } from 'beaker-kernel';
import BeakerNotebook from './components/BeakerNotebook.vue';

const settings = {
    baseUrl: process.env.VUE_APP_BASE_URL,
    appUrl: process.env.VUE_APP_URL,
    wsUrl: process.env.VUE_APP_WS_URL,
    token: process.env.VUE_APP_TOKEN,
};

//
const rawSession = new BeakerSession(
  {
    settings: settings,
    name: "MyKernel",
    kernelName: "beaker_kernel",
    sessionId: "dev_session",
  }
);

const connectionStatus = ref('connecting');
const debug_logs = reactive([]);

provide('debug_logs', debug_logs);


rawSession.sessionReady.then(() => {

    rawSession.session.iopubMessage.connect((session, msg) => {

        if (msg.header.msg_type === "code_cell") {
            beakerSession.addCodeCell(msg.content.code);
        }
        else if (msg.header.msg_type === 'status') {
          setTimeout(() => {
            const newStatus = msg?.content?.execution_state || 'connecting';
            connectionStatus.value = newStatus == 'idle' ? 'connected' : newStatus;
          }, 1000);
        } else if (msg.header.msg_type === "debug_event") {
            debug_logs.push(msg.content);
        } 
        
        // else if (msg.header.msg_type === 'context_info_response') {
        //   console.log('context_info_response', msg.content);
        // } else {
        //   console.log('msg type', msg);
        // }

    })
    beakerSession.addCodeCell("import pandas as pd\ndf = pd.DataFrame([[1,2,3,4,5,6.7], [2,3,4,5,6,7,8]])\ndf.plot()")
    // beakerSession.addCodeCell("import pandas as pd\ndf = pd.DataFrame([[1,2,3,4,5,6.7], [2,3,4,5,6,7,8]])\ndf.plot()")
    // beakerSession.addCodeCell("import pandas as pd\ndf = pd.DataFrame([[1,2,3,4,5,6.7], [2,3,4,5,6,7,8]])\ndf.plot()")
    // beakerSession.addCodeCell("import pandas as pd\ndf = pd.DataFrame([[1,2,3,4,5,6.7], [2,3,4,5,6,7,8]])\ndf.plot()")
    // beakerSession.addCodeCell("import pandas as pd\ndf = pd.DataFrame([[1,2,3,4,5,6.7], [2,3,4,5,6,7,8]])\ndf.plot()")

});

onBeforeMount(() => {
  document.title = "Beaker Development Interface"
});

const beakerSession = reactive(rawSession);


</script>

<style lang="scss">
#app {
  margin: 0;
  padding: 0;
  overflow: hidden;
}
</style>
