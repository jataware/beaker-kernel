<template>
  <div class="beaker-session-container">
    <slot></slot>
  </div>
</template>

<script lang="ts">
import { reactive, ref, inject, provide, VNode } from 'vue';
import { ComponentPublicInstance } from '@vue/runtime-core';
import { BeakerSession, JupyterMimeRenderer  } from 'beaker-kernel';
// import { type IActiveContextInfo } from 'beaker-kernel/util';
import * as messages from '@jupyterlab/services/lib/kernel/messages';
import BeakerCell from '@/components/cell/BeakerCell.vue'


export interface IBeakerSession extends ComponentPublicInstance {
  activeContext: any,
  connectionSettings: any,
  defaultKernel: string,
  renderers,
  session: BeakerSession,
  sessionId: string,
  sessionName: string,
  status,

  fetchContextInfo: () => any,
  findNotebookCell: (any) => any,
  findNotebookCellById: (any) => any,
  setContext: () => void,
}

// eslint-disable-next-line
// @ts-ignore: setupState is not defined in the Vue type definition, but seems to reliably exist, and it's ok if it doesn't.
const getCellData = (vnode: VNode) => (vnode?.props?.cell || vnode?.component?.setupState?.cell || undefined);

const isCell = (vnode: VNode) => {
  return (
    getCellData(vnode) !== undefined
    && vnode.component.exposed?.execute !== undefined
    && vnode.component.exposed?.enter !== undefined
  )
}

export default {
  props: {
      "connectionSettings": Object,
      "sessionName": String,
      "sessionId": String,
      "defaultKernel": String,
      "renderers": Object,
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


    // const activeContext = ref<IActiveContextInfo | undefined>(undefined);
    const activeContext = ref();

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

    rawSession.sessionReady.then(() => {

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
    }
  },

  methods: {
    findNotebookCell(predicate: ((BeakerCell) => boolean)) {
      const subtree = this.$.subTree;
      const children = [...subtree.dynamicChildren];
      while (children.length > 0) {
        const child = children.splice(0, 1)[0];
        if (isCell(child) && predicate(child)) {
          return {...child.component?.proxy, ...child.component?.exposeProxy};
        }
        if (Array.isArray(child.component?.subTree?.children) ) {
          children.push(...child.component.subTree.children);
        }
        if (Array.isArray(child.children)) {
          children.push(...child.children);
        }
      }
    },

    findNotebookCellById(id: string): typeof BeakerCell {
      return this.findNotebookCell((vnode) => (getCellData(vnode).id === id));
    },

    async fetchContextInfo() {
      const activeContextInfo = await this.session.activeContext();
      this.activeContext = activeContextInfo;
      this.$emit("context-changed", this.activeContext);
    },

    setContext(contextPayload: any) {
        const showToast: (...args) => void = inject('show_toast');
        // TODO: Figure out a better way set context to "loading" state
        this.activeContext = {};

        const future = this.session.sendBeakerMessage(
            "context_setup_request",
            contextPayload
        );
        future.done.then((result: any) => {

            if (result?.content?.status === 'error') {
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

            if (result?.content?.status === 'abort') {
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
            this.fetchContextInfo();
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
    this.fetchContextInfo();
  },
}
</script>

<style lang="scss">
</style>
