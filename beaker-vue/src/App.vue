<template>
    <BeakerNotebook :session="beakerSession" :connectionStatus="connectionStatus" />
</template>

<script setup lang="ts">
import { reactive, ref, onBeforeMount } from 'vue';
import { BeakerSession } from 'beaker-kernel';
import BeakerNotebook from './components/BeakerNotebook.vue';

// TODO: Move the config outside this file. Fetch from environment?
const settings = {
    baseUrl: "http://localhost:8080",
    appUrl: "http://localhost:8080",
    wsUrl: "ws://localhost:8080",
    token: "89f73481102c46c0bc13b2998f9a4fce",
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


rawSession.sessionReady.then(() => {

    rawSession.session.iopubMessage.connect((session, msg) => {

        // TODO msg.header.msg_type === "status" -> change status of Beaker-ui header?

        if (msg.header.msg_type === "code_cell") {
            beakerSession.addCodeCell(msg.content.code);
        }
        else if (msg.header.msg_type === 'status') {
          setTimeout(() => {
            const newStatus = msg?.content?.execution_state || 'connecting';
            connectionStatus.value = newStatus == 'idle' ? 'connected' : newStatus;
          }, 1000);
        } 
        // TODO set this in context tree
         else if (msg.header.msg_type === "context_setup_response") {
            console.log('context setup:', msg);
        // TODO add this to logging pane
        } else if (msg.header.msg_type === "debug_event") {
            console.log('debug event:', msg);
        }
        else {
          console.log('msg type', msg.header.msg_type);
        }

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
