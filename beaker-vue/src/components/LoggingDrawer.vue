<template>

  <Menubar
      :model="footerMenuItems"
      breakpoint="800"
   />

  <transition name="slide">
    <div class="logging-pane" v-if="isLogOpen">

      <div class="pane-contents">
        <div class="actions">
          <span>TODO</span>
        </div>

        <div class="data-container">
          <div class="scroller-area">

          </div>
        </div>
      </div>
    </div>
  </transition>

</template>

<script setup lang="ts">

import { ref, computed, defineProps, inject } from "vue";

// import VueJsonPretty from 'vue-json-pretty';
// import 'vue-json-pretty/lib/styles.css1rem;

// import Button from 'primevue/button';
import Menubar from 'primevue/menubar';
// import InputText from 'primevue/inputtext';
// import { Codemirror } from "vue-codemirror";
// import { oneDark } from '@codemirror/theme-one-dark';

// TODO MenuBar has a pass-through (pt) prop where can can
// pass in context and set/fix the `active` tab to logging permanently
// while the logging drawer is open. Right now the pane remains open when
// the button goes back to looking "unpress".

const isLogOpen = ref(false);

// const props = defineProps([
//   'theme'
// ]);

const upstream_logs = inject('debug_logs');

// const debug_logs = computed(() => {
//   return JSON.stringify(upstream_logs, undefined, 2);
// });

// const codeExtensions = computed(() => {
//     const ext = [];
//     if (props.theme === 'dark') {
//         ext.push(oneDark);
//     }
//     return ext;
// });


// TODO should probably add handlers for Help|Terms|Contact
// Can also rename this file and make mor generic than Logging since it contains
// all "footer" links/actions
const footerMenuItems = ref([
    {
        label: 'Help',
        icon: 'pi pi-question',
        command: () => {
            isLogOpen.value = !isLogOpen.value;
        }
    },
    {
        label: 'About',
        icon: 'pi pi-bookmark',
    },
    {
        label: 'Terms',
        icon: 'pi pi-book'
    },
    {
        label: 'Contact',
        icon: 'pi pi-envelope'
    }
]);


</script>

<style lang="scss" scoped>

.logging-pane {
  width: 100%;
  height: 19rem;
  padding: 0.5rem;
  margin: 0;
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
  transition: all 0.6s ease-out;
}
.slide-leave-active {
  transition: all 0.4s linear;
}

.slide-enter-from {
  height: 0;
}
.slide-enter-to {
  height: 19rem;
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
