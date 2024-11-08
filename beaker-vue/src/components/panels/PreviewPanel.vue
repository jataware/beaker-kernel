<template>
    <div class="preview-container pre">
        <!-- <div class="preview-container-header">
            {{ props }}
        </div> -->
        <div class="preview-container-main">
            <div class="pdf-preview" v-if="mime === 'application/pdf'">
                <PDFPreview :url="url" :sidebarCallback="sidebarCallback"/>
            </div>
        </div>
    </div>
</template>
  
<script lang="ts" setup>
import { ref, defineProps, watch, computed } from "vue";

import PDFPreview from "../render/pdf/PDFPreview.vue";

const fallbackMime = ref(null)

const props = defineProps(['url', 'mimetype', 'sidebarCallback'])

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
        console.log("a'")
        fallbackMime.value = await getMimeFromURL(props.url);
        return;
    }
    fallbackMime.value = undefined;
})

</script>

<style lang="scss">

</style>
