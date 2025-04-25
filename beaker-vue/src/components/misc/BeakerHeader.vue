<template>
    <Toolbar class="beaker-toolbar">
        <template #start>
            <SessionStatus
                :connection-status="beakerSession.status"
            />
            <Button
                v-if="showContextSelection"
                outlined
                size="small"
                icon="pi pi-angle-down"
                iconPos="right"
                class="connection-button"
                @click="selectKernel"
                :label="beakerSession.activeContext?.slug"
                :loading="loading"
                v-tooltip.bottom="$tmpl._('select_kernel_tooltip', 'Change or update the context')"
            />
            <Button
                text
                size="small"
                v-else-if="loading"
                :loading=loading
                :disabled="true"

                v-tooltip.bottom="'Connecting'"
            />
        </template>

        <template #center>
            <div class="title">
                <img
                    v-if="$tmpl.hasAsset('header_logo')"
                    class="header-logo"
                    :src="$tmpl.getAsset('header_logo').src"
                    v-bind="$tmpl.getAsset('header_logo').attrs"
                />
                <h4>
                    {{ title ?? "Beaker Notebook" }}
                </h4>
                <span v-if="titleExtra" class="title-extra">{{ titleExtra }}</span>
            </div>
        </template>

        <template #end>
            <nav class="flex">
                <template v-for="navItem in navItems" :key="navItem">
                    <a
                        v-if="navItem.type === 'link'"
                        :href="navItem.href"
                        :aria-label="navItem.label"
                        :rel="navItem.rel"
                        :target="navItem.target"
                        v-tooltip.bottom="navItem.label"
                        style="margin: auto"
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
import { defineProps, defineEmits, computed, inject, withDefaults, getCurrentInstance, getCurrentScope } from "vue";
import Toolbar from 'primevue/toolbar';
import Button from 'primevue/button';
import { BeakerSessionComponentType } from '../session/BeakerSession.vue';
import { IBeakerTheme } from '../../plugins/theme';
import SessionStatus from "../session/SessionStatus.vue";

interface BeakerHeaderProps {
    title: string;
    titleExtra?: string;
    nav?: any[];
}


const props = withDefaults(defineProps<BeakerHeaderProps>(), {
    title: "Beaker",
});

const emit = defineEmits(["selectKernel"]);

const { theme, toggleDarkMode } = inject<IBeakerTheme>('theme');
const beakerSession = inject<BeakerSessionComponentType>("beakerSession");
const beakerApp = inject<any>("beakerAppConfig");

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

const loading = computed(() => {
    return !(beakerSession.activeContext?.slug);
})

const showContextSelection = computed(() => {
    // Always show on dev page
    if (beakerApp?.currentPage?.value === "dev") {
        return true;
    }
    // Hide on non-dev pages single_context is set on the default context
    if (beakerApp?.config?.default_context?.single_context === true) {
        return false;
    }
    // Default to show
    return true;
})

</script>

<script lang="ts">
import { Component } from 'vue';
export interface NavOption {
    type: "button"|"link";
    href?: string
    icon?: string;
    label?: string;
    component?: Component;
    componentStyle?: {[key: string]: string};
    command?: () => void;
}
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

    .header-logo {
        max-height: 30px;
        margin-right: 20px;
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

.beaker-toolbar .title h4 {
    white-space: nowrap;
}

</style>
