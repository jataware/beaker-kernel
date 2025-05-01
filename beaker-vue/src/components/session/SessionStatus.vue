<template>
    <div class="status-container">
        <span class="pi pi-circle-fill status-indicator" :class="status" />
        <span class="status-label">{{ statusLabel }}</span>
        <Button
            v-if="status === 'dead' || status === 'disconnected'"
            v-tooltip="'Reconnect'"
            class="reconnect-button"
            size="small"
            icon="pi pi-refresh"
            :outlined="true"
            text
            @click="beakerSession.reconnect()"
        />
    </div>
</template>

<script setup lang="ts">
import { computed, inject, capitalize } from "vue";
import Button from 'primevue/button';
import type { BeakerSessionComponentType } from '../session/BeakerSession.vue';

// TODO too many granular props- use a slot instead?
const props = defineProps([
    "connectionStatus",
    "loading",
    "kernel"
]);

const beakerSession = inject<BeakerSessionComponentType>("beakerSession");

const status = computed(() => props.connectionStatus || beakerSession.status);

const loading = computed(() => {
    return props.loading || !(beakerSession.activeContext?.slug);
})

const statusLabels = {
    "idle": "Ready",
    "dead": "Disconnected",
}

const statusLabel = computed<string>(() => (statusLabels[status.value] || capitalize(status.value || "")));

</script>

<style lang="scss">

.status-container {
    display: flex;
    line-height: inherit;
    align-items: center;
    justify-content: start;
    color: var(--text-color);
    min-width: 9rem;
    padding-left: 0.5rem;
    margin-right: 1rem;
}

.status-indicator {
    font-size: inherit;
    margin-right: 0.5rem;

    &.connected {
        color: var(--green-300);
    }
    &.starting {
        color: var(--green-400);
    }
    &.idle {
        color: var(--green-400);
    }
    &.connecting, &.starting {
        color: var(--green-200);
    }
    &.reconnecting {
        color: var(--orange-300);
    }
    &.busy, &.terminating {
        color: var(--orange-400);
    }
    &.dead, &.disconnected {
        color: var(--pink-300);
    }
    &.restarting, &.terminating, &.autorestarting {
        color: var(--orange(600))
    }
}

.status-label {
    // padding-right: 0.75rem;
}

.connection-button {
    color: var(--surface-500);
}

.reconnect-button {
    color: var(--pink-500);
}

</style>
