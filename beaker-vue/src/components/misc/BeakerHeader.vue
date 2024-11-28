<template>
    <Toolbar class="beaker-toolbar">
        <template #start>
            <div class="status-bar">
                <span v-tooltip.right="'Kernel connection status'">
                    <i class="pi pi-circle-fill" :style="`font-size: inherit; color: var(--${connectionColor});`" />
                    {{ statusLabel }}
                </span>
            </div>
            <Button
                outlined
                size="small"
                icon="pi pi-angle-down"
                iconPos="right"
                class="connection-button"
                @click="selectKernel"
                :label="beakerSession.activeContext?.slug"
                :loading="loading"
                v-tooltip.bottom="'Change or update the context'"
            />
        </template>

        <template #center>
            <div class="title">
                <h4>
                    {{ title || "Beaker Development Interface" }}
                </h4>
                <span v-if="titleExtra" class="title-extra">{{ titleExtra }}</span>
            </div>
        </template>

        <template #end>
            <nav>
                <template v-for="navItem in navItems" :key="navItem">
                    <a
                        v-if="navItem.type === 'link'"
                        :href="navItem.href"
                        :aria-label="navItem.label"
                        :rel="navItem.rel"
                        :target="navItem.target"
                        v-tooltip.bottom="navItem.label"
                    >
                        <Button
                            :icon="navItem.icon ? `pi pi-${navItem.icon}`: 'pi'"
                            text
                        >
                            <component
                                :item="navItem"
                                v-if="navItem.component"
                                :is="navItem.component"
                                :style="navItem.componentStyle"
                            />
                        </Button>
                    </a>
                    <Button v-else-if="navItem.type === 'button'"
                        :icon="`pi pi-${navItem.icon}`"
                        text
                        @click="navItem.command"
                        :aria-label="navItem.label"
                        v-tooltip.bottom="navItem.label"
                    />
                </template>
            </nav>
        </template>
    </Toolbar>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, computed, inject, withDefaults } from "vue";
import Toolbar from 'primevue/toolbar';
import Button from 'primevue/button';
import { BeakerSessionComponentType } from '../session/BeakerSession.vue';
import { IBeakerTheme } from '../../plugins/theme';

export interface Props {
    title: string;
    titleExtra?: string;
    nav?: any[];
}

const props = withDefaults(defineProps<Props>(), {
    title: "Beaker",
});

const emit = defineEmits(["selectKernel"]);

const { theme, toggleDarkMode } = inject<IBeakerTheme>('theme');
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");

const navItems = computed(() => {
    if (props.nav) {
        return props.nav;
    }
    return [
        {
            type: 'button',
            icon: (theme.mode === 'dark' ? 'sun' : 'moon'),
            command: toggleDarkMode,
            label: `Switch to ${theme.mode === 'dark' ? 'light' : 'dark'} mode.`,
        },
        {
            type: 'link',
            href: `https://jataware.github.io/beaker-kernel`,
            label: 'Beaker Documentation',
            icon: "book",
            rel: "noopener",
            target: "_blank",
        },
        {
            type: 'link',
            href: `https://github.com/jataware/beaker-kernel`,
            label: 'Check us out on Github',
            icon: "github",
            rel: "noopener",
            target: "_blank",
        },
    ];
})

function selectKernel() {
    emit('selectKernel');
}

const themeIcon = computed(() => {
    return `pi pi-${theme.mode === 'dark' ? 'sun' : 'moon'}`;
});

const loading = computed(() => {
    return !(beakerSession.activeContext?.slug);
})

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

.beaker-toolbar {
    width: 100%;
    padding: 0 0.5rem;
    border-radius: 0;

    &.p-toolbar {
        flex-wrap: nowrap;
    }
    .p-toolbar-group-end {
        margin-left: -0.5rem;
    }

    button {
        padding: 0.5em;
    }

    .title {
        font-size: 1.2rem;
        padding: 0 0.5rem;
        display: flex;
        align-items: center;

        font-weight: 500;
        color: var(--gray-500);

        h4 {
            display: inline-block;
            font-size: 1.8rem;
            margin: 0;
            padding: 0;

            @media(max-width: 885px) {
                .longer-title {
                    display: none;
                }
            }
        }

        .title-extra {
            margin-left: 1rem;
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
    padding: 0.5em;
}

</style>
