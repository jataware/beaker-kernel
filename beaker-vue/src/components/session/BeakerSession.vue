<template>
  <div class="beaker-session-container">
    <slot></slot>
  </div>
</template>

<script lang="ts">
import { reactive, ref, inject, provide, VNode, defineComponent, PropType, ComponentInternalInstance, DefineComponent } from 'vue';
import { BeakerSession, IBeakerRendererOptions, IMimeRenderer, IBeakerCell } from 'beaker-kernel/src';
import { BeakerRenderOutput } from '../../renderers';
import * as messages from '@jupyterlab/services/lib/kernel/messages';


export interface IBeakerCellComponent {
  [key: string]: any,
  $: ComponentInternalInstance,
  cell: IBeakerCell,
  enter: () => void,
  exit: () => void,
  execute: () => void,
  clear: () => void,
}


export const toBeakerCellComponent = (vnode: VNode): IBeakerCellComponent => {
  const component: ComponentInternalInstance = vnode?.component;
  if (component === undefined) {
    return undefined;
  }
  return reactive({
    ...component.proxy as unknown as {cell: IBeakerCell},
    ...component.exposed as {enter: ()=>void, exit: ()=>void, execute: ()=>void, clear: ()=>void},
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
  ],

  setup(props, { emit }) {

    const status = ref("unknown");

    const cellRegistry = ref<({[key: string]: VNode})>({});

    const activeContext = ref();
    const notebookComponent = ref();

    const rawSession = new BeakerSession(
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

    rawSession.sessionReady.then(async () => {

      rawSession.session.iopubMessage.connect((session, msg) => {
        emit("iopub-msg", msg);
        if (messages.isStatusMsg(msg)) {
          const newStatus = msg?.content?.execution_state || 'connecting';
          status.value = newStatus;
          emit("session-status-changed", newStatus);
        }
      });
      rawSession.session.session.anyMessage.connect((_: unknown, {msg, direction}) => {
        emit("any-msg", msg, direction);
      });
      rawSession.session.unhandledMessage.connect((session, msg) => {
        emit("unhandled-msg", msg);
      });
    });

    const beakerSession = reactive(rawSession);


    return {
      activeContext,
      session: beakerSession,
      status,
      cellRegistry,
      notebookComponent,
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
