<template>
    <BeakerNotebook :session="beakerSession" :connectionStatus="connectionStatus" />
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
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

    setTimeout(() => {
      connectionStatus.value = 'connected';
    }, 400);

    rawSession.session.iopubMessage.connect((session, msg) => {

        if (msg.header.msg_type === "code_cell") {
            connectionStatus.value = 'busy';
            beakerSession.addCodeCell(msg.content.code);

            setTimeout(() => {
              connectionStatus.value = 'connected';
            }, 1000);
        }

    })
    beakerSession.addCodeCell("import pandas as pd\ndf = pd.DataFrame([[1,2,3,4,5,6.7], [2,3,4,5,6,7,8]])\ndf.plot()")
    // beakerSession.addCodeCell("import pandas as pd\ndf = pd.DataFrame([[1,2,3,4,5,6.7], [2,3,4,5,6,7,8]])\ndf.plot()")
    // beakerSession.addCodeCell("import pandas as pd\ndf = pd.DataFrame([[1,2,3,4,5,6.7], [2,3,4,5,6,7,8]])\ndf.plot()")
    // beakerSession.addCodeCell("import pandas as pd\ndf = pd.DataFrame([[1,2,3,4,5,6.7], [2,3,4,5,6,7,8]])\ndf.plot()")
    // beakerSession.addCodeCell("import pandas as pd\ndf = pd.DataFrame([[1,2,3,4,5,6.7], [2,3,4,5,6,7,8]])\ndf.plot()")

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
