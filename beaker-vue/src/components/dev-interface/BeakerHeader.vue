<template>
    <Toolbar class="toolbar">
        <template #start>
            <div class="status-bar">
                <i class="pi pi-circle-fill" :style="`font-size: inherit; color: var(--${connectionColor});`" />
                {{ statusLabel }}
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
                    @click="toggleDarkMode"
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
import { defineProps, defineEmits, computed, inject, getCurrentInstance } from "vue";
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

const { theme, toggleDarkMode } = inject('theme');
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");

function selectKernel() {
    emit('selectKernel');
}

const themeIcon = computed(() => {
    return `pi pi-${theme === 'dark' ? 'sun' : 'moon'}`;
});

const statusLabels = {
    unknown: 'Unknown',
    starting: 'Starting',
    idle: 'Ready',
    busy: 'Busy',
    terminating: 'Terminating',
    restarting: 'Restarting',
    autorestarting: 'Autorestarting',
    dead: 'Dead',
    // This extends kernel status for now.
    connected: 'Connected',
    connecting: 'Connecting'
}

const statusColors = {
    connected: 'green-300',
    idle: 'green-400',
    connecting: 'green-200',
    busy: 'orange-400',
};

const statusLabel = computed(() => {
    return statusLabels[beakerSession.status] || "unknown";

});

const connectionColor = computed(() => {
    // return connectionStatusColorMap[beakerSession.status];
    return statusColors[beakerSession.status] || "grey-200"
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
