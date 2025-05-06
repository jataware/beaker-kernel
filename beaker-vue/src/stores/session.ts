import { ref, computed, reactive } from 'vue'
import { defineStore } from 'pinia'

export const useSessionStore = defineStore('beakerSession', () => {
  // const status = ref<BeakerKernelStatus>("unknown");

  // const cellRegistry = ref<({[key: string]: VNode})>({});

  // const activeContext = ref();
  // const notebookComponent = ref();

  // const rawSession: BeakerSession = new BeakerSession(
  //   {
  //     settings: props.connectionSettings,
  //     name: props.sessionName,
  //     sessionId: props.sessionId,
  //     kernelName: props.defaultKernel,
  //     rendererOptions: {
  //       renderers: props.renderers || [],
  //     },
  //     context: props.context,
  //   }
  // );

  // status.value = "connecting";

  // rawSession.services.connectionFailure.connect((serviceManager, error) => {
  //   emit('connection-failure', error);
  //   console.log("Error connecting to kernel/api", error);
  // })

  // const setSignalHandlers = async (session) => {
  //     session.iopubMessage.connect((session, msg) => {
  //       emit("iopub-msg", msg);
  //       if (messages.isStatusMsg(msg)) {
  //         const newStatus = msg?.content?.execution_state || 'unknown';
  //         status.value = rawSession.status;
  //         emit("session-status-changed", newStatus);
  //       }
  //     });
  //     session.session.anyMessage.connect((_: unknown, {msg, direction}) => {
  //       emit("any-msg", msg, direction);
  //     });
  //     session.unhandledMessage.connect((session, msg) => {
  //       emit("unhandled-msg", msg);
  //     });
  //     session.connectionStatusChanged.connect((session, connectionStatus: JupyterConnectionStatus) => {
  //       status.value = rawSession.status;
  //     });
  //   }

  //   rawSession?.sessionReady.then(async () => {
  //     await setSignalHandlers(rawSession.session);
  //   });

  // const beakerSession = reactive(rawSession);



  return {
    // activeContext,
    // session: beakerSession,
    // status,
    // cellRegistry,
    // notebookComponent,
    // setSignalHandlers,
  }
})
