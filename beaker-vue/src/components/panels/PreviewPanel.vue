<template>
    <Sidebar 
        v-model:visible="visible" 
        position="right" 
        :style="`width: ${width}px;`"
        :modal="false"
        :dismissable="false"
        ref="sidebar"
    >
        <template #container="{ closeCallback }">
            <div class="preview-container-pre">
                <div 
                    class="preview-draggable" 
                    :style="`width: ${dragWidth}px;`"
                    @mousedown.left.prevent="hookResize()"
                />
                <div 
                    class="preview-container-main"
                     :style="`max-width: calc(100% - ${dragWidth}px);`"
                >
                    <div class="pdf-preview" v-if="mime === 'application/pdf'">
                        <PDFPreview :url="url" :sidebarCallback="closeCallback"/>
                    </div>
                </div>
            </div>
        </template>
    </Sidebar>
</template>
  
<script lang="ts" setup>
import { ref, defineProps, watch, computed, defineModel } from "vue";

import PDFPreview from "../render/pdf/PDFPreview.vue";
import Sidebar from "primevue/sidebar";

const fallbackMime = ref(null)
const sidebar = ref();

const hookResize = () => {
    const resize = event => {
        const target = window.innerWidth - (event.x - dragWidth.value / 2);
        width.value = Math.min(Math.max(target, minWidth), window.innerWidth * 0.9);
    };
    const unhookResize = () => {
        document.querySelector('body').removeEventListener('mousemove', resize);
        document.querySelector('body').removeEventListener('mouseup', this);
    };
    document.querySelector('body').addEventListener('mousemove', resize);
    document.querySelector('body').addEventListener('mouseup', unhookResize);
}


// drag bar width in px
const dragWidth = ref(5);
// default pdfjs canvas plus dragbar size
const width = ref(614 + dragWidth.value);
const minWidth = 260;

const props = defineProps([
    'url', 
    'mimetype'
])

const visible = defineModel<boolean>();

const mime = computed(() => props.mimetype ?? fallbackMime.value)

const getMimeFromURL = async (url: string): Promise<string> => 
    fetch(url).then(response => response.headers.get('Content-Type'))
              .catch(error => { 
                    console.log(error);
                    return null;
                })

watch(() => [props.url, props.mimetype], async (f, s) => {
    // if no associated mimetype, find a fallback
    console.log(props.mimetype)
    if (props.mimetype === undefined || props.mimetype == null) {
        fallbackMime.value = await getMimeFromURL(props.url);
        return;
    }
    fallbackMime.value = undefined;
})

</script>

<style lang="scss">
.preview-container-pre {
    display: flex;
    flex-direction: row;
    height: 100%;
}
.preview-draggable {
    width: 3px;
    min-height: 100%;
    z-index: 100;
    background-color: var(--surface-b);
}
.preview-draggable:hover {
    cursor: col-resize;
}
.preview-container-main {
    flex: 1;
    // if pdf controls are integrated here, remove border, but don't change default control bar styling
    .pdf-preview .controls-container div.p-toolbar {
        border: none;
        border-radius: 0;
        flex-wrap: nowrap;
        .p-toolbar-group-start button.pdf-ui-close {
            margin-left: 0;
        }
    }
}
</style>
