<template>
  <div class="beaker-session-container">
    <slot></slot>
  </div>
</template>

<script lang="ts">
import { reactive, ref, inject, provide, VNode, defineComponent, PropType, ComponentInternalInstance, DefineComponent } from 'vue';
import CodeEditor from '../misc/CodeEditor.vue';
import { BeakerSession, IMimeRenderer, IBeakerCell } from 'beaker-kernel/src';
import { BeakerKernelStatus } from 'beaker-kernel/src/session';
import * as messages from '@jupyterlab/services/lib/kernel/messages';
import { ConnectionStatus as JupyterConnectionStatus } from '@jupyterlab/services/lib/kernel/kernel';


export interface IBeakerCellComponent {
  [key: string]: any,
  $: ComponentInternalInstance,
  cell: IBeakerCell,
  enter: (position?: "start" | "end" | number) => void,
  exit: () => void,
  execute: () => void,
  clear: () => void,
  editor?: typeof CodeEditor,
}


export const toBeakerCellComponent = (vnode: VNode): IBeakerCellComponent => {
  const component: ComponentInternalInstance = vnode?.component;
  if (component === undefined) {
    return undefined;
  }
  return reactive({
    // @
    ...{
      cell: (component.proxy as unknown as {cell: IBeakerCell}).cell,
    },
    ...{
      enter: component.exposed.enter,
      exit: component.exposed.exit,
      execute: component.exposed.execute,
      clear: component.exposed.clear,
      editor: component.exposed.editor,
    } as {
      enter: (position?: "start" | "end" | number)=>void,
      exit: ()=>void,
      execute: ()=>void,
      clear: ()=>void,
      editor?: typeof CodeEditor,
    },
    $: component,
  });
}

export const BeakerSessionComponent: DefineComponent<any, any, any> = defineComponent({
  props: {
      connectionSettings: Object,
      sessionName: String,
      sessionId: String,
      defaultKernel: String,
      renderers: (Object as any as PropType<IMimeRenderer<HTMLElement>[]>),
      context: {
        type: Object as PropType<{
          slug: string,
          payload: any,
        }>,
        required: false,
      },
  },

  emits: [
      "iopub-msg",
      "unhandled-msg",
      "any-msg",
      "session-status-changed",
      "context-changed",
      "connection-failure",
  ],

  setup(props, { emit }) {

    const status = ref<BeakerKernelStatus>("unknown");

    const cellRegistry = ref<({[key: string]: VNode})>({});

    const activeContext = ref();
    const notebookComponent = ref();

    const rawSession: BeakerSession = new BeakerSession(
      {
        settings: props.connectionSettings,
        name: props.sessionName,
        sessionId: props.sessionId,
        kernelName: props.defaultKernel,
        rendererOptions: {
          renderers: props.renderers || [],
        },
        context: props.context,
      }
    );
    rawSession.services.connectionFailure.connect((serviceManager, error) => {
      emit('connection-failure', error);
      console.log("Error connecting to kernel/api", error);
    })

    const setSignalHandlers = async (session) => {
        session.iopubMessage.connect((session, msg) => {
          emit("iopub-msg", msg);
          if (messages.isStatusMsg(msg)) {
            const newStatus = msg?.content?.execution_state || 'unknown';
            status.value = rawSession.status;
            emit("session-status-changed", newStatus);
          }
        });
        session.session.anyMessage.connect((_: unknown, {msg, direction}) => {
          emit("any-msg", msg, direction);
        });
        session.unhandledMessage.connect((session, msg) => {
          emit("unhandled-msg", msg);
        });
        session.connectionStatusChanged.connect((session, connectionStatus: JupyterConnectionStatus) => {
          status.value = rawSession.status;
        });
      }

      rawSession?.sessionReady.then(async () => {
        await setSignalHandlers(rawSession.session);
      });

    const beakerSession = reactive(rawSession);



    return {
      activeContext,
      session: beakerSession,
      status,
      cellRegistry,
      notebookComponent,
      setSignalHandlers,
    }
  },

  methods: {
    findNotebookCell(predicate: ((cell: IBeakerCellComponent) => boolean)): IBeakerCellComponent {
      for (const cellVnode of this.cellRegistry) {
        if (predicate(cellVnode)) {
          return toBeakerCellComponent(cellVnode)
        }
      }
    },

    findNotebookCellById(id: string): IBeakerCellComponent {
      const cellVnode = this.cellRegistry[id];
      if (cellVnode !== undefined) {
        return toBeakerCellComponent(cellVnode);
      }
    },

    async updateContextInfo() {
      const activeContextInfo = await this.session.activeContext();
      this.activeContext = activeContextInfo;
      this.$emit("context-changed", this.activeContext);
    },

    setContext(contextPayload: any) {
        const showToast: (...args) => void = inject('show_toast');
        // TODO: Figure out a better way set context to "loading" state
        this.activeContext = {};

        const future = this.session.setContext(contextPayload);
        future.then((result: any) => {

            if (result?.status === 'error') {
                let formatted = result?.content?.evalue;
                if (formatted) {
                    const endsWithPeriod = /\.$/.test(formatted);
                    if (!endsWithPeriod) {
                        formatted += '.';
                    }
                }
                showToast({
                    title: 'Context Setup Failed',
                    severity: 'error',
                    detail: `${formatted} Please try again or contact us.`,
                    life: 0
                });
                return;
            }

            if (result?.status === 'abort') {
                showToast({
                    title: 'Context Setup Aborted',
                    severity: 'warning',
                    detail: result?.content?.evalue,
                    life: 6000
                });
                return;
            }

            // Close the context dialog
            // contextSelectionOpen.value = false;
            // Update the context info in the sidebar
            // TODO: Is this even needed? Could maybe be fed/triggered by existing events?
            this.updateContextInfo();
        });
        return future;
    },

    async reconnect() {
      const newSession = await this.session.reconnect();
      await this.setSignalHandlers(newSession);
      this.setContext({
        context: this.activeContext.slug,
        context_info: this.activeContext.config,
        language: this.activeContext.language.slug,
        debug: this.activeContext.info.debug,
        verbose: this.activeContext.info.verbose,
      });

    },
  },

  beforeMount() {
    // Register session dependencies for injection (Must be in beforeMount to be available to children)
    provide('beakerSession', reactive(this));
    provide('session', this.session);
  },

  mounted() {
    this.updateContextInfo();
  },
});

export type BeakerSessionComponentType = InstanceType<typeof BeakerSessionComponent>;

export default BeakerSessionComponent;

</script>

<style lang="scss">
</style>
