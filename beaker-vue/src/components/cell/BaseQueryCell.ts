import { ref, shallowRef, inject, computed, nextTick, getCurrentInstance } from "vue";
import { BeakerSession } from 'beaker-kernel/src';
import { BeakerSessionComponentType } from "../session/BeakerSession.vue";

export const useBaseQueryCell = (props) => {
    const cell = shallowRef(props.cell);
    const isEditing = ref<boolean>(cell.value.source === "");
    const promptEditorMinHeight = ref<number>(100);
    const promptText = ref<string>(cell.value.source);
    const response = ref("");
    const textarea = ref();
    const session: BeakerSession = inject("session");
    const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
    const instance = getCurrentInstance();
  
    const events = computed(() => {
      return [...props.cell.events];
    });
  
    function execute() {
      const config: any = instance?.root?.props?.config;
      const sendNotebookState = config ? config.extra?.send_notebook_state : undefined;
      cell.value.source = promptText.value;
      isEditing.value = false;
      nextTick(() => {
        const future = props.cell.execute(session, sendNotebookState);
        future.registerMessageHook(
          (msg) => {
            msg.cell = cell.value;
          }
        )
      });
    }
  
    function enter(position?: "start" | "end" | number) {
      if (!isEditing.value) {
        isEditing.value = true;
      }
      if (position === "start") {
        position = 0;
      }
      else if (position === "end") {
        position = textarea.value?.$el?.value.length || -1;
      }
      nextTick(() => {
        textarea.value?.$el?.focus();
        textarea.value.$el.setSelectionRange(position, position);
      });
    }
  
    function exit() {
      if (promptText.value === cell.value.source) {
        isEditing.value = false;
      }
      else {
        textarea.value?.$el?.blur();
      }
    }
  
    function clear() {
      cell.value.source = "";
      isEditing.value = true;
      promptEditorMinHeight.value = 100;
      promptText.value = "";
      response.value = "";
    }
  
    function respond() {
      if (!response.value.trim()) {
        return;
      }
      props.cell.respond(response.value, session);
      response.value = "";
    }
  
    return {
      cell,
      isEditing,
      promptEditorMinHeight,
      promptText,
      response,
      textarea,
      session,
      beakerSession,
      events,
      execute,
      enter,
      exit,
      clear,
      respond
    };
  };