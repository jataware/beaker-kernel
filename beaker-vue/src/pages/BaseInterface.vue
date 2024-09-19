<template>
    <BeakerSession id="beaker-session-container" ref="beakerSession">
        <app>
            <header>
                <slot name="header">
                    <BeakerHeader
                        :connectionStatus="connectionStatus"
                        :loading="!activeContext?.slug"
                        @select-kernel="toggleContextSelection"
                        :title="props.title"
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
        </app>
    </BeakerSession>
</template>

<script setup lang="ts">
import { defineProps, ref, onBeforeMount, provide, nextTick, onUnmounted, defineExpose } from 'vue';
import BeakerSession from '../components/session/BeakerSession.vue';
import BeakerHeader from '../components/dev-interface/BeakerHeader.vue';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';

import BeakerContextSelection from "../components/session/BeakerContextSelection.vue";
import FooterDrawer from '../components/dev-interface/FooterDrawer.vue';


const toast = useToast();

const activeContext = ref();
const beakerNotebookRef = ref();


// TODO -- WARNING: showToast is only defined locally, but provided/used everywhere. Move to session?
// Let's only use severity=success|warning|danger(=error) for now
const showToast = ({title, detail, life=3000, severity=('success' as undefined), position='bottom-right'}) => {
    toast.add({
        summary: title,
        detail,
        life,
        // for options, seee https://primevue.org/toast/
        severity,
        // position
    });
};

const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.has("session") ? urlParams.get("session") : "dev_session";

const props = defineProps([
    "title",
]);

const connectionStatus = ref('connecting');
const saveInterval = ref();
const beakerSession = ref<typeof BeakerSession>();

const contextSelectionOpen = ref(false);
const contextProcessing = ref(false);

const toggleContextSelection = () => {
    contextSelectionOpen.value = !contextSelectionOpen.value;
};


onBeforeMount(() => {
    var notebookData: {[key: string]: any};
    try {
        notebookData = JSON.parse(localStorage.getItem("notebookData")) || {};
    }
    catch (e) {
        console.error(e);
        notebookData = {};
    }

    if (notebookData[sessionId]?.data) {
        nextTick(() => {
            if (beakerNotebookRef.value?.notebook) {
                beakerNotebookRef.value?.notebook.loadFromIPynb(notebookData[sessionId].data);
                nextTick(() => {
                    beakerNotebookRef.value?.selectCell(notebookData[sessionId].selectedCell);
                });
            }
        });
    }
    saveInterval.value = setInterval(snapshot, 30000);
    window.addEventListener("beforeunload", snapshot);
});

onUnmounted(() => {
    clearInterval(saveInterval.value);
    saveInterval.value = null;
    window.removeEventListener("beforeunload", snapshot);
});

// TODO: See above. Move somewhere better.
provide('show_toast', showToast);

const snapshot = () => {
    var notebookData: {[key: string]: any};
    try {
        notebookData = JSON.parse(localStorage.getItem("notebookData")) || {};
    }
    catch (e) {
        console.error(e);
        notebookData = {};
    }
    // Only save state if there is state to save
    if (beakerNotebookRef.value?.notebook) {
        notebookData[sessionId] = {
            data: beakerNotebookRef.value?.notebook.toIPynb(),
            selectedCell: beakerNotebookRef.value?.selectedCellId,
        };
        localStorage.setItem("notebookData", JSON.stringify(notebookData));
    }
};

defineExpose({
    beakerSession,
});

</script>

<style lang="scss">
#beaker-session-container {
    height: 100vh;
    width: 100vw;
    display: flex;
    flex-direction: column;
}

app {
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
