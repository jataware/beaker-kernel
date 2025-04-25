<template>
    <!-- <VerticalToolbar style="align-self: flex-start;">
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
    <transition name="slide"> -->
        <!-- <div class="help-pane" v-if="isAboutOpen" :class="isAboutOpen ? 'help-pane-open' : 'help-pane-closed'"> -->
        <div class="help-pane help-pane-open">
            <div>
                <h3>Beaker Chat</h3>
                <h3>Help</h3>
                <h4>Setting the Context:</h4>
                <p>Use the filled circle in the top left to open context selection.</p>
                <h4>Changing to Notebook View:</h4>
                <p>Use the last button on the left toolbar to switch back and forth in different views.</p>
                <h3>About</h3>
                <p>Placeholder text here.</p>
            </div>
        </div>
    <!-- </transition> -->
</template>

<script setup lang="ts">
import VerticalToolbar from '../chat-interface/VerticalToolbar.vue';
import Button from 'primevue/button';
import { ref } from "vue";
const isAboutOpen = ref(false);
</script>

<style lang="scss" scoped>

.help-pane {
    // display: flex;
    // flex-direction: row;
    // gap: 4rem;
    // padding: 0.5rem;
    // margin: 0;
    // & > div {
    //     min-width: 24rem;
    //     overflow: hidden;
    //     position: relative;
    // }
}

// .help-pane-closed {
//     width: 0rem;
// }

// .help-pane-open {
//     width: 24rem;
// }


.slide-enter-active {
    transition: width 0.1s ease-out;
}

.slide-leave-active {
    transition: width 0.1s ease-out;
}

.slide-enter-from {
    width: 0;
}

.slide-enter-to {
    width: 24rem;
}

.slide-leave-to {
    width: 0;
}

</style>
