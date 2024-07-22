<template>
    <Toolbar class="toolbar">
        <template #start>
            <div class="status-bar">
                <i class="pi pi-circle-fill" :style="`font-size: inherit; color: var(--${connectionColor});`" />
                {{capitalize(beakerSession?.status || "Huh?")}}
            </div>
            <Button
                outlined
                size="small"
                icon="pi pi-angle-down"
                iconPos="right"
                class="connection-button"
                @click="selectKernel"
                :label="beakerSession.activeContext?.slug"
                :loading="!(beakerSession.activeContext?.slug)"
            />
        </template>

        <template #center>
            <div class="logo">
                <h4>
                    Beaker <span class="longer-title">Development Interface</span>
                </h4>
            </div>
        </template>

        <template #end>
            <nav>
                <Button
                    text
                    @click="props.toggleDarkMode"
                    style="margin: 0; color: var(--gray-500);"
                    :icon="themeIcon"
                />
                <a
                    href="https://jataware.github.io/beaker-kernel"
                    rel="noopener"
                    target="_blank"
                >
                    <Button
                        text
                        style="margin: 0; color: var(--gray-500);"
                        aria-label="Beaker Documentation"
                        icon="pi pi-book"
                    />
                </a>
                <a
                    href="https://github.com/jataware/beaker-kernel"
                    rel="noopener"
                    target="_blank"
                >
                    <Button
                        text
                        style="margin: 0; color: var(--gray-500);"
                        aria-label="Github Repository Link Icon"
                        icon="pi pi-github"
                    />
                </a>
            </nav>
        </template>
    </Toolbar>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, computed, inject } from "vue";
import Toolbar from 'primevue/toolbar';
import Button from 'primevue/button';
import { capitalize } from '../../util';
import { BeakerSessionComponentType } from '@/components/session/BeakerSession.vue';

// TODO too many granular props- use a slot instead?
const props = defineProps([
    "toggleDarkMode",
    "kernel"
]);

const emit = defineEmits(["selectKernel"]);

const theme = inject('theme');
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
console.log(beakerSession);

function selectKernel() {
    emit('select-kernel');
}

const themeIcon = computed(() => {
    return `pi pi-${theme === 'dark' ? 'sun' : 'moon'}`;
});


// TODO export/import from ts-lib utils.ts
// enum KernelState {
// 	unknown = 'unknown',
// 	starting = 'starting',
// 	idle = 'idle',
// 	busy = 'busy',
// 	terminating = 'terminating',
// 	restarting = 'restarting',
// 	autorestarting = 'autorestarting',
// 	dead = 'dead',
//   // This extends kernel status for now.
//   connected = 'connected',
//   connecting = 'connecting'
// }

const KernelState = {
	unknown: 'unknown',
	starting: 'starting',
	idle: 'idle',
	busy: 'busy',
	terminating: 'terminating',
	restarting: 'restarting',
	autorestarting: 'autorestarting',
	dead: 'dead',
  //:his extends kernel status for now.
  connected: 'connected',
  connecting: 'connecting'
}

const connectionStatusColorMap = {
    [KernelState.connected]: 'green-400',
    // [KernelState.idle]: 'green-400',
    [KernelState.connecting]: 'green-200',
    [KernelState.busy]: 'orange-400',
};

const connectionColor = computed(() => {
    return connectionStatusColorMap[beakerSession.status];
});

</script>

<style lang="scss">

.toolbar {
    width: 100%;
    padding: 0.5rem 1rem;

    &.p-toolbar {
        flex-wrap: nowrap;
    }
    .p-toolbar-group-end {
        margin-left: -0.5rem;
    }

    .logo {
        font-size: 1.5rem;
        padding: 0 0.5rem;
        h4 {
            font-size: 1.8rem;
            margin: 0;
            padding: 0;
            font-weight: 500;
            color: var(--gray-500);

            @media(max-width: 885px) {
                .longer-title {
                    display: none;
                }
            }
        }
    }

}

.status-bar {
    display: flex;
    line-height: inherit;
    align-items: center;
    color: var(--text-color);
    width: 8rem;
    & > i {
        margin-right: 0.5rem;
    }
}

.connection-button {
    color: var(--surface-500);
}

</style>
