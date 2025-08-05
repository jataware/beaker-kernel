<template>
    <Button
        icon="pi pi-times"
        class="image-zoom-close"
        @click="closeZoom"
        aria-label="Close zoom"
        severity="secondary"
    />
    <div class="image-zoom-container">
        <div
            class="image-zoom-content"
            ref="imageContainer"
            @wheel.prevent="handleWheelZoom"
            @mousedown="startPan"
            @mousemove="handlePan"
            @mouseup="stopPan"
            @mouseleave="stopPan"
        >
                <!-- v-show="show" -->
            <img
                ref="zoomedImage"
                :src="data.imageSrc"
                :alt="data.imageAlt"
                :style="{
                    transform: `scale(${zoomLevel}) translate(${panX}px, ${panY}px)`,
                    cursor: isPanning ? 'grabbing' : 'grab',
                }"
            />
        </div>
        <div class="image-zoom-controls">
            <Button
                icon="pi pi-minus"
                class="zoom-btn zoom-out"
                @click="zoomOut"
                :disabled="zoomLevel <= 0.25"
                aria-label="Zoom out"
                severity="secondary"
            />
            <span class="zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
            <Button
                icon="pi pi-plus"
                class="zoom-btn zoom-in"
                @click="zoomIn"
                :disabled="zoomLevel >= 4"
                aria-label="Zoom in"
                severity="secondary"
            />
            <Button
                class="zoom-btn zoom-reset"
                @click="resetZoom"
                aria-label="Reset zoom"
                severity="secondary"
                label="Reset"
            />
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, inject, onMounted } from 'vue';
import type { Ref } from 'vue';
import Button from 'primevue/button';
import type { DynamicDialogInstance } from 'primevue/dynamicdialogoptions';

const emit = defineEmits<{
    close: [];
}>();

const dialogRef = inject<Ref<DynamicDialogInstance>>('dialogRef');
const data = ref({
    imageSrc: null,
    imageAlt: "Zoomed image",
    ...dialogRef.value.data,
});

onMounted(() => {
    calculateFitZoom();
});

const show = ref(false);
const zoomLevel = ref<number|null>(1);
const fitZoomLevel = ref<number|null>(1);
const panX = ref(0);
const panY = ref(0);
const isPanning = ref(false);
const lastPanX = ref(0);
const lastPanY = ref(0);

const imageContainer = ref<HTMLElement>();
const zoomedImage = ref<HTMLImageElement>();

// calculates the zoom level that fits the entire image
const calculateFitZoom = () => {
    if (!zoomedImage.value || !imageContainer.value) return;

    const img = zoomedImage.value;
    const container = imageContainer.value;

    const imageWidth = img.naturalWidth;
    const imageHeight = img.naturalHeight;

    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;

    const scaleX = containerWidth / imageWidth;
    const scaleY = containerHeight / imageHeight;

    // don't zoom beyond 100% initially
    const fitZoom = Math.min(scaleX, scaleY, 1);

    fitZoomLevel.value = fitZoom;
    zoomLevel.value = fitZoom;
};

const closeZoom = () => {
    dialogRef.value?.close();
};

const zoomIn = () => {
    if (zoomLevel.value < 4) {
        zoomLevel.value = Math.min(zoomLevel.value * 1.25, 4);
    }
};

const zoomOut = () => {
    const minZoom = Math.min(0.25, fitZoomLevel.value);
    if (zoomLevel.value > minZoom) {
        zoomLevel.value = Math.max(zoomLevel.value * 0.8, minZoom);
    }
};

const resetZoom = () => {
    zoomLevel.value = fitZoomLevel.value;
    panX.value = 0;
    panY.value = 0;
};

const handleWheelZoom = (event: WheelEvent) => {
    const delta = event.deltaY > 0 ? 0.9 : 1.1;
    const newZoom = Math.max(0.25, Math.min(4, zoomLevel.value * delta));
    zoomLevel.value = newZoom;
};

const startPan = (event: MouseEvent) => {
    isPanning.value = true;
    lastPanX.value = event.clientX;
    lastPanY.value = event.clientY;
    event.preventDefault();
};

const handlePan = (event: MouseEvent) => {
    if (isPanning.value) {
        const deltaX = event.clientX - lastPanX.value;
        const deltaY = event.clientY - lastPanY.value;

        panX.value += deltaX / zoomLevel.value;
        panY.value += deltaY / zoomLevel.value;

        lastPanX.value = event.clientX;
        lastPanY.value = event.clientY;
    }
};

const stopPan = () => {
    isPanning.value = false;
};

</script>

<style lang="scss" scoped>
.image-zoom-container {
    flex: 1;
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.image-zoom-close {
    position: absolute;
    top: -3rem;
    right: 0;
    z-index: 10;

    --p-button-secondary-background: var(--p-surface-b);
    --p-button-secondary-border-color: var(--p-surface-h);

    &:focus {
        outline: 2px solid #007bff;
        outline-offset: 2px;
    }
}

.image-zoom-controls {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    justify-content: center;
    padding: 8px 12px;
    border-radius: 6px;

    .zoom-btn {
        background-color: var(--p-surface-a);
        &:focus {
            outline: 2px solid #007bff;
            outline-offset: 1px;
        }
        &.zoom-reset {
            font-size: 12px;
        }
    }

    .zoom-level {
        color: var(--p-surface-h);
        font-size: 14px;
        font-weight: bold;
        min-width: 45px;
        text-align: center;
    }
}

.image-zoom-content {
    border: 2px inset var(--p-surface-e);
    overflow: hidden;
    display: flex;
    flex: 1;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    user-select: none;

    img {
        object-fit: none;
        transition: transform 0.1s ease-out;
        transform-origin: center;
    }
}
</style>
