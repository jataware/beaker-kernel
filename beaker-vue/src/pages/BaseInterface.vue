<template>
    <BeakerSession id="beaker-session-container" ref="beakerSession">
        <div id="app">
            <header>
                <slot name="header">
                    <BeakerHeader
                        :connectionStatus="connectionStatus"
                        @select-kernel="toggleContextSelection"
                        :title="props.title"
                        :title-extra="props.titleExtra"
                        :nav="props.headerNav"
                    />
                </slot>
            </header>

            <main>
                <slot name="main">
                    <div id="left-panel">
                        <slot name="left-panel">
                        </slot>
                    </div>

                    <div id="center-panel">
                        <slot>
                        </slot>
                    </div>

                    <div id="right-panel">
                        <slot name="right-panel">
                        </slot>
                    </div>
                </slot>
            </main>

            <footer>
            <slot name="footer">
                <FooterDrawer />
            </slot>
            </footer>

            <!-- Modals, popups and globals -->
            <slot name="context-selection-popup">
                <BeakerContextSelection
                    :isOpen="contextSelectionOpen"
                    :toggleOpen="toggleContextSelection"
                    :contextProcessing="contextProcessing"
                    @context-changed="(contextData) => {beakerSession.setContext(contextData)}"
                    @close-context-selection="contextSelectionOpen = false"
                />
            </slot>
            <slot name="toast">
                <Toast position="bottom-right" />
            </slot>
        </div>
        <slot name="login-dialog">
            <Dialog v-model:visible="authDialogVisible" modal header="OpenAI auth error" style="max-width: 45vw;">
                <div style="margin-bottom: 1rem;">
                    The OpenAI service requires a valid authentication key.
                </div>
                <div v-if="authMessage" style="margin-bottom: 1rem;">
                    Message from service:<br/>
                    <span style="font-style: italic;">{{ authMessage }}</span>
                </div>

                <div style="margin-bottom: 1rem;">
                    Please provide a valid API key to continue. It will not be used for this session but will not be saved.
                </div>

                <InputGroup>
                    <InputText type="password" v-model="authDialogEntry" placeholder="OpenAI key" @keydown.enter="setApiKey" autofocus/>
                    <Button icon="pi pi-check" @click="setApiKey"/>
                </InputGroup>

            </Dialog>
        </slot>
    </BeakerSession>
</template>

<script setup lang="ts">
import { defineEmits, defineProps, ref, onMounted, provide, nextTick, onUnmounted, toRaw, defineExpose } from 'vue';
import Dialog from 'primevue/dialog';
import BeakerSession from '../components/session/BeakerSession.vue';
import BeakerHeader from '../components/dev-interface/BeakerHeader.vue';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';
import {BeakerSession as Session} from 'beaker-kernel/src'
import InputText from 'primevue/inputtext';
import InputGroup from 'primevue/inputgroup';
import Button from 'primevue/button';
import sum from 'hash-sum';

import BeakerContextSelection from "../components/session/BeakerContextSelection.vue";
import FooterDrawer from '../components/dev-interface/FooterDrawer.vue';


const toast = useToast();

const lastSaveChecksum = ref<string>();


// TODO -- WARNING: showToast is only defined locally, but provided/used everywhere. Move to session?
interface ShowToastOptions {
    title: string;
    detail: string;
    life?: number;
    severity?: 'success' | 'warn' | 'info' | 'error';
}

const showToast = (options: ShowToastOptions) => {
    const {title, detail, life=3000, severity='success'} = options;
    toast.add({
        summary: title,
        detail,
        life,
        severity,
    });
};

const props = defineProps([
    "title",
    "titleExtra",
    "savefile",
    "headerNav",
    "apiKeyPrompt",
]);

const emit = defineEmits([
    "notebook-autosaved",
    "open-file",
]);

const connectionStatus = ref('connecting');
const saveInterval = ref();
const beakerSession = ref<typeof BeakerSession>();
const authDialogVisible = ref<boolean>(props.apiKeyPrompt || false);
const authDialogEntry = ref<string>("");
const authMessage = ref<string>("");
const authRetryCell = ref();

const contextSelectionOpen = ref(false);
const contextProcessing = ref(false);

const toggleContextSelection = () => {
    contextSelectionOpen.value = !contextSelectionOpen.value;
};

provide('show_toast', showToast);

onMounted(async () => {
    const session: Session = beakerSession.value.session;
    await session.sessionReady;  // Ensure content service is up

    var notebookData: {[key: string]: any};
    try {
        notebookData = JSON.parse(localStorage.getItem("notebookData")) || {};
    }
    catch (e) {
        console.error(e);
        notebookData = {};
    }

    // Connect listener for authentication message
    session.session.ready.then(() => {
        const sessionContext = toRaw(session.session.session)
        sessionContext.iopubMessage.connect(iopubMessage);
    });

    const sessionId = session.sessionId;

    const sessionData = notebookData[sessionId];
    if (sessionData) {
        nextTick(async () => {
            if (sessionData.filename !== undefined) {

                const contentsService = session.services.contents;
                const result = await contentsService.get(sessionData.filename)
                lastSaveChecksum.value = sessionData.checksum;
                emit('open-file', result.content, result.path, {selectedCell: sessionData.selectedCell});
            }
            else if (sessionData.data !== undefined) {
                emit('open-file', sessionData.data, undefined, {selectedCell: sessionData.selectedCell});
            }
            if (sessionData.selectedCell !== undefined && beakerSession.value.notebookComponent) {
                nextTick(() => beakerSession.value.notebookComponent.selectCell(sessionData.selectedCell));
            }
        });
    }
    saveInterval.value = setInterval(snapshot, 30000);
    window.addEventListener("beforeunload", snapshot);
});

const iopubMessage = (_sessionConn, msg) => {
    if (msg.header.msg_type === "llm_auth_failure") {
        authDialogVisible.value = true;
        authMessage.value = msg.content.msg;
        if (msg.cell !== undefined) {
            authRetryCell.value = msg.cell;
        }
    }
};

const setApiKey = async () => {
    const apiKey = authDialogEntry.value;
    if (apiKey.length == 0) {
        return;
    }
    const session = beakerSession.value.session;
    await session.sendBeakerMessage("llm_set_key", {
        api_key: apiKey
    });
    authDialogVisible.value = false;
    if (authRetryCell.value) {
        console.log(authRetryCell);
        authRetryCell.value.execute(session);
    }
}

onUnmounted(() => {
    clearInterval(saveInterval.value);
    saveInterval.value = null;
    window.removeEventListener("beforeunload", snapshot);
});

const snapshot = async () => {
    var notebookData: {[key: string]: any};
    try {
        notebookData = JSON.parse(localStorage.getItem("notebookData")) || {};
    }
    catch (e) {
        console.error(e);
        notebookData = {};
    }

    const session: Session = beakerSession.value.session;
    const sessionId = session.sessionId ;

    if (!Object.keys(notebookData).includes(sessionId)) {
        notebookData[sessionId] = {};
    }
    const sessionData = notebookData[sessionId];

    // Only save state if there is state to save
    if (session.notebook) {
        sessionData['data'] = session.notebook.toIPynb();
        const notebookComponent = beakerSession.value.notebookComponent;
        if (notebookComponent) {
            sessionData['selectedCell'] = notebookComponent.selectedCellId
        }

        if (props.savefile && typeof props.savefile === "string") {

            const notebookContent = session.notebook.toIPynb();
            const notebookChecksum: string = sum(notebookContent);

            if (!lastSaveChecksum.value || lastSaveChecksum.value != notebookChecksum) {
                lastSaveChecksum.value = notebookChecksum;

                const contentsService = session.services.contents;
                const path = props.savefile;
                const result = await contentsService.save(path, {
                    type: "notebook",
                    content: notebookContent,
                    format: 'text',
                });
                emit("notebook-autosaved", result.path);
                showToast({
                    title: "Autosave",
                    detail: `Auto-saved notebook to file ${props.savefile}.`,
                });
                sessionData['filename'] = result.path;
                sessionData['checksum'] = notebookChecksum;
            }
        }
        else {
            const notebookContent = session.notebook.toIPynb();
            const notebookChecksum: string = sum(notebookContent);
            sessionData['filename'] = undefined;
            sessionData['data'] = notebookContent;
            sessionData['checksum'] = notebookChecksum;
        }
        localStorage.setItem("notebookData", JSON.stringify(notebookData));
    }
};

defineExpose({
    beakerSession,
    showToast,
});

</script>

<style lang="scss">
#beaker-session-container {
    height: 100vh;
    width: 100vw;
    display: flex;
    flex-direction: column;
}

#app {
    margin: 0;
    padding: 0;
    overflow: hidden;
    height: 100vh;
    width: 100vw;
    display: grid;
    grid-template:
        "header" max-content
        "main" 1fr
        "footer" max-content /
        100%;
}

header {
    grid-area: header;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

main {
    grid-area: main;
    position: relative;
    display: grid;
    grid-template:
        "left-panel center-panel right-panel" 100% /
        min-content minmax(30%, 100%) min-content;
    background-color: var(--surface-0);
    overflow: hidden auto;
    max-width: 100%;
    max-height: 100%;
}

footer {
    grid-area: footer;
}

#left-panel {
    grid-area: left-panel;
    width: 100%;
}

#center-panel {
    grid-area: center-panel;
    border: 1px solid;
    border-color: var(--surface-border);

}

#right-panel {
    grid-area: right-panel;
    width: 100%;
}

</style>
