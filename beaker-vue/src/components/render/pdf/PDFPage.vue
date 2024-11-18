<template>
    <div ref="pdfContainer" class="pdf-container">
      <canvas ref="canvas" class="pdf-canvas"></canvas>
    </div>
</template>

<script setup>
import { ref, onMounted, watch, defineProps, defineExpose } from 'vue';
import { getDocument } from 'pdfjs-dist';

const loadPdfjs = async function () { 
    const pdfjs = await import("pdfjs-dist/build/pdf"); 
    pdfjs.GlobalWorkerOptions.workerSrc = new URL(
        "pdfjs-dist/build/pdf.worker.mjs",
        import.meta.url
    ).toString(); 
};

const props = defineProps({
    url: {
        type: [String],
        required: true,
    },
    scale: {
        type: Number,
        default: 1.0,
    },
    page: {
        type: Number,
        default: 1,
    },
    sidebarCallback: {
        type: Object
    }
});

const pdfContainer = ref(null);
const canvas = ref(null);
let pdfDoc = null;

// lock when rendering
const isLoading = ref(false);
const pagesRef = ref(null)

const renderPage = async (pageNum) => {
    if (!pdfDoc) return;

    isLoading.value = true;
    const page = await pdfDoc.getPage(pageNum);
    const viewport = page.getViewport({ scale: props.scale });
    const context = canvas.value.getContext('2d');
    canvas.value.width = viewport.width;
    canvas.value.height = viewport.height;
    const renderContext = {
        canvasContext: context,
        viewport: viewport,
    };
    await page.render(renderContext).promise;
    isLoading.value = false;
};

const loadPdf = async () => {
    if (typeof props.url === 'object' && props.url instanceof File) {
        const fileReader = new FileReader();
        fileReader.readAsArrayBuffer(props.url);
        fileReader.onload = async (event) => {
            pdfDoc = await getDocument({ data: event.target.result }).promise;
            pagesRef.value = pdfDoc?._pdfInfo?.numPages;
            renderPage(props.page);
        };
    } else if (typeof props.url === 'string') {
        pdfDoc = await getDocument(props.url).promise;
        pagesRef.value = pdfDoc?._pdfInfo?.numPages;
        renderPage(props.page);
    }
};

defineExpose({pages: pagesRef, isLoading: isLoading});

onMounted(async () => {
    await loadPdfjs();
    await loadPdf();
});

watch(() => [props.url], loadPdf);
watch(() => [props.scale, props.page], () => renderPage(props.page));

</script>

<style scoped>
    .pdf-container {
        display: flex;
        /* should only apply when canvas width < element width. otherwise breaks scroll. */
        /* justify-content: center;
        align-items: center; */
        overflow: auto;
    }
    .pdf-canvas {
        border: 1px solid #ddd;
        width: auto;
    }
</style>
