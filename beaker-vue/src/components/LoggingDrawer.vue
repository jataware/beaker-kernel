<template>

    <Menubar
        :model="footerMenuItems"
        breakpoint="800"
     />

  <transition name="slide">
    <div class="logging-pane" v-if="isLogOpen">

      <div class="pane-contents">
        <div class="actions">
          <div class="p-input-icon-left" style="padding: 0; margin: 0;">
              <i class="pi pi-search" />
              <InputText size="small" placeholder="Filter" style="margin: 0;" />
          </div>
          &nbsp;
          &nbsp;
          &nbsp;
          <Button 
            label="Clear"
            severity="warning"
            size="small"
          />
        </div>

        <div class="data-container">
        <pre>
  [I 2024-01-25 11:41:59.000 NotebookApp] Writing notebook server cookie secret to /run/user/1000/jupyter/notebook_cookie_secret
  [I 2024-01-25 11:41:59.000 NotebookApp] Serving notebooks from local directory: /home/user
  [I 2024-01-25 11:41:59.000 NotebookApp] Jupyter Notebook 6.4.5 is running at:
  [I 2024-01-25 11:41:59.000 NotebookApp] http://localhost:8888/?token=1234567890abcdef
  [I 2024-01-25 11:41:59.000 NotebookApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).
  [C 2024-01-25 11:41:59.000 NotebookApp] 
    
    To access the notebook, open this URL in a browser:
       http://localhost:8888/?token=1234567890abcdef
  [I 2024-01-25 11:42:03.000 NotebookApp] Creating new notebook in 
  [I 2024-01-25 11:42:03.000 NotebookApp] Writing notebook-signing key to /home/user/.local/share/jupyter/notebook_secret
  [W 2024-01-25 11:42:03.000 NotebookApp] Notebook Untitled.ipynb is not trusted
  [I 2024-01-25 11:42:04.000 NotebookApp] Kernel started: 0987654321fedcba
  [I 2024-01-25 11:42:07.000 NotebookApp] Adapting from protocol version 5.1 (kernel 0987654321fedcba) to 5.3 (client).
        </pre>
        </div>
      </div>
    </div>
  </transition>

</template>

<script setup lang="ts">

import { ref, onBeforeMount, onMounted, defineProps, computed, Component } from "vue";
import Card from 'primevue/card';
import Button from 'primevue/button';
import Menubar from 'primevue/menubar';
import InputText from 'primevue/inputtext';
import Toolbar from 'primevue/toolbar';


const isLogOpen = ref(false);

const footerMenuItems = ref([
    {
        label: 'Help',
        icon: 'pi pi-question'
    },
    {
        label: 'Logging',
        icon: 'pi pi-search',
        command: () => {
            // toast.add({ severity: 'warn', summary: 'Search Results', detail: 'No results found', life: 3000 });
            isLogOpen.value = !isLogOpen.value;
            console.log('open logging panel', isLogOpen.value);
        }
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


// const props = defineProps([
//     "isOpen"
// ]);

const logs = [];

</script>

<style lang="scss" scoped>

.logging-pane {
  width: 100%;
  height: 14rem;
  padding: 0.5rem;
  margin: 0;
}

.data-container {
  position: relative;
  flex: 1;
  padding: 0.25rem 0;
  margin: 0;
}

.slide-enter-active {
  transition: all 0.6s ease;
}
.slide-leave-active {
  transition: all 0.3s ease;
}

pre {
  display: block;
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  overflow: auto;
  padding: 0.5rem;
  border: 1px solid lightgray;
  border-radius: 3px;
  color: #494949
}

.slide-enter-from {
  height: 0;
}
.slide-enter-to {
  height: 14rem;
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
