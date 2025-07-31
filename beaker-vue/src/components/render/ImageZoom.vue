<template>
    <div
        v-if="isVisible"
        class="image-zoom-overlay"
        @keydown.esc="closeZoom"
        tabindex="0"
    >
        <div class="image-zoom-container" @click.stop>
            <Button
                icon="pi pi-times"
                class="image-zoom-close"
                @click="closeZoom"
                aria-label="Close zoom"
                severity="secondary"
            />

            <div
                class="image-zoom-content"
                ref="imageContainer"
                @wheel.prevent="handleWheelZoom"
                @mousedown="startPan"
                @mousemove="handlePan"
                @mouseup="stopPan"
                @mouseleave="stopPan"
            >
                <img
                    ref="zoomedImage"
                    :src="imageSrc"
                    :alt="imageAlt"
                    :style="{
                        transform: `scale(${zoomLevel}) translate(${panX}px, ${panY}px)`,
                        cursor: isPanning ? 'grabbing' : 'grab'
                    }"
                    @load="handleImageLoad"
                />
            </div>
            <div class="image-zoom-controls" v-if="showZoomControls">
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
    </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import Button from 'primevue/button';

interface Props {
    isVisible: boolean;
    imageSrc: string;
    imageAlt?: string;
    showZoomControls?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
    imageAlt: 'Zoomed image',
    showZoomControls: true
});

const emit = defineEmits<{
    close: [];
}>();

const zoomLevel = ref(1);
const fitZoomLevel = ref(1);
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
    emit('close');
    resetZoom();
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

const handleImageLoad = () => {
    nextTick(() => {
        calculateFitZoom();
        const overlay = document.querySelector('.image-zoom-overlay') as HTMLElement;
        overlay?.focus();
    });
};

watch(() => props.imageSrc, () => {
    // zoomLevel recalculated in handleImageLoad
    fitZoomLevel.value = 1;
    resetZoom();
});

watch(() => props.isVisible, (visible) => {
    if (!visible) {
        resetZoom();
    } else {
        // recalculate fit zoom when becoming visible, container size changed
        nextTick(() => {
            calculateFitZoom();
        });
    }
});
</script>

<style lang="scss" scoped>
.image-zoom-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 999;
    backdrop-filter: blur(3px);
    &:focus {
        outline: none;
    }
}

.image-zoom-container {
    position: relative;
    max-width: 95vw;
    max-height: 95vh;
    display: flex;
    flex-direction: column;
}

.image-zoom-close {
    position: absolute;
    top: -45px;
    right: 0;
    z-index: 10001;

    background-color: var(--p-surface-a);

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
        color: white;
        font-size: 14px;
        font-weight: bold;
        min-width: 45px;
        text-align: center;
    }
}

.image-zoom-content {
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    max-width: 90vw;
    max-height: 80vh;
    border-radius: 8px;
    user-select: none;

    img {
        object-fit: none;
        transition: transform 0.1s ease-out;
        transform-origin: center;
    }
}
</style>
