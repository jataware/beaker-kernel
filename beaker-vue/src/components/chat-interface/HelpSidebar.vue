<template>
    <VerticalToolbar style="align-self: flex-start;">
        <template #start>
            <Button
                @click="isAboutOpen = !isAboutOpen"
                v-tooltip.left="{value: 'About', showDelay: 300}"
                icon="pi pi-question"
                size="small"
                severity="info"
                text
            />
        </template>
    </VerticalToolbar>
    <transition name="slide">
        <div class="help-pane" v-if="isAboutOpen">
            <div>
                <h3>About</h3>
                <p>TODO - Add some kind of description</p>
            </div>
        </div>
    </transition>
</template>

<script setup lang="ts">
import VerticalToolbar from '@/components/chat-interface/VerticalToolbar.vue';
import Button from 'primevue/button';
import { ref } from "vue";
const isAboutOpen = ref(false);
</script>

<style lang="scss" scoped>

.help-menu-bar {
    &.p-menubar {
        padding: 0 0.5rem;
    }
}

.help-pane {
    display: flex;
    flex-direction: row;
    gap: 4rem;
    width: 100%;
    height: 15rem;
    padding: 0.5rem;
    margin: 0;
    & > div {
        position: relative;
    }
    & > div:not(:first-child)::before {
        content: ' ';
        width: 0.2rem;
        position: absolute;
        top: 0;
        bottom: 0;
        left: -2.1rem;
        background-color: var(--surface-b);
        box-shadow: var(--surface-b) 0px 0px 4px;
    }
}

.data-container {
    position: relative;
    flex: 1;
    padding: 0.25rem 0;
    margin: 0;
}

.scroller-area {
    display: block;
    position: absolute;
    top: 0;
    bottom: 1rem;
    left: 0;
    right: 0;
    overflow: auto;
    padding: 0.5rem;
    margin-top: 0.5rem;
    border: 1px solid lightgray;
    border-radius: 3px;
    color: var(--text-color-secondary);
}

.slide-enter-active {
    transition: height 0.6s ease-out;
}

.slide-leave-active {
    transition: height 0.4s linear;
}

.slide-enter-from {
    height: 0;
}

.slide-enter-to {
    height: 15rem;
}

.slide-leave-to {
    height: 0;
}

.pane-contents {
    display: flex;
    flex-direction: column;
    height: inherit;
}

.actions {
    width: 100%;
    display: flex;
    justify-content: space-between;
    padding-bottom: 0;
    margin-bottom: 0;
}
</style>