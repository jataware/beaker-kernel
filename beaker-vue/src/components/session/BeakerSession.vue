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
import { defineProps, reactive, ref, inject, provide, defineEmits, onMounted, defineExpose } from 'vue';
import { BeakerSession, JupyterMimeRenderer  } from 'beaker-kernel';
import { type IActiveContextInfo } from 'beaker-kernel/util';
import * as messages from '@jupyterlab/services/lib/kernel/messages';

const showToast = inject('show_toast');

const props = defineProps([
  "connectionSettings",
  "sessionName",
  "sessionId",
  "defaultKernel",
  "renderers",

]);

const emit = defineEmits([
  "iopub-msg",
  "unhandled-msg",
  "any-msg",
  "session-status-changed",
  "context-changed",
]);

const activeContext = ref<IActiveContextInfo | undefined>(undefined);

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

const fetchContextInfo = async () => {
  const activeContextInfo = await beakerSession.activeContext();
  activeContext.value = activeContextInfo;
  emit("context-changed", activeContext.value);
}

const setContext = (contextPayload: any) => {
    // TODO: Figure out a better way set context to "loading" state
    activeContext.value = {};

    const future = beakerSession.sendBeakerMessage(
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
        fetchContextInfo();
    });
}


provide('session', beakerSession);
provide('active_context', activeContext);

onMounted(() => {
  fetchContextInfo();
});

defineExpose({
  setContext
});

</script>

<style lang="scss">
</style>
