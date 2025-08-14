<template>
        <div class="playground-container">
            <Card class="theme-showcase">
                <template #title>
                    <div class="showcase-header">
                        <h2>Beaker Theme Color Palette</h2>
                        <Button 
                            :icon="`pi ${isDarkMode ? 'pi-sun' : 'pi-moon'}`"
                            @click="toggleTheme"
                            text
                            rounded
                            v-tooltip.bottom="`Switch to ${isDarkMode ? 'light' : 'dark'} mode`"
                        />
                    </div>
                </template>
                <template #content>
                    <div class="color-sections">
                        <section class="color-section">
                            <h3>Primary Colors</h3>
                            <div class="color-grid">
                                <div class="color-card" v-for="(value, key) in primaryColors" :key="key">
                                    <div class="color-swatch" :style="{backgroundColor: `var(--p-${key})`}"></div>
                                    <div class="color-info">
                                        <code class="color-name">--p-{{ key }}</code>
                                        <span class="color-value" :style="{color: `var(--p-${key})`}">●</span>
                                    </div>
                                </div>
                            </div>
                        </section>

                        <!-- surfaces -->
                        <section class="color-section">
                            <h3>Surface Colors</h3>
                            <div class="color-grid">
                                <div class="color-card" v-for="surface in surfaceColors" :key="surface">
                                    <div class="color-swatch" :style="{backgroundColor: `var(--p-surface-${surface})`}"></div>
                                    <div class="color-info">
                                        <code class="color-name">--p-surface-{{ surface }}</code>
                                        <span class="color-value" :style="{color: `var(--p-surface-${surface})`}">●</span>
                                    </div>
                                </div>
                            </div>
                        </section>

                        <!-- text -->
                        <section class="color-section">
                            <h3>Text Colors</h3>
                            <div class="color-grid">
                                <div class="color-card" v-for="textColor in textColors" :key="textColor">
                                    <div class="color-swatch text-demo" :style="{backgroundColor: 'var(--p-surface-a)', color: `var(--${textColor})`}">
                                        Sample Text
                                    </div>
                                    <div class="color-info">
                                        <code class="color-name">--{{ textColor }}</code>
                                        <span class="color-value" :style="{color: `var(--${textColor})`}">●</span>
                                    </div>
                                </div>
                            </div>
                        </section>

                        <!-- semantic -->
                        <section class="color-section">
                            <h3>Semantic Colors & Others</h3>
                            <div class="semantic-colors">
                                <div v-for="(colors, colorName) in semanticColors" :key="colorName" class="semantic-group">
                                    <h4 class="semantic-title">{{ colorName.charAt(0).toUpperCase() + colorName.slice(1) }}</h4>
                                    <div class="color-row">
                                        <div class="color-card small" v-for="shade in colors" :key="shade">
                                            <div class="color-swatch small" :style="{backgroundColor: `var(--p-${colorName}-${shade})`}"></div>
                                            <div class="color-info small">
                                                <code class="color-name small">--p-{{ colorName }}-{{ shade }}</code>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </section>

                        <!-- component specific (didnt work) -->
                        <!-- <section class="color-section">
                            <h3>Component-Specific Colors</h3>
                            <div class="color-grid">
                                <div class="color-card" v-for="compColor in componentColors" :key="compColor">
                                    <div class="color-swatch" :style="{backgroundColor: `var(--p-${compColor})`}"></div>
                                    <div class="color-info">
                                        <code class="color-name">--p-{{ compColor }}</code>
                                        <span class="color-value" :style="{color: `var(--p-${compColor})`}">●</span>
                                    </div>
                                </div>
                            </div>
                        </section> -->

                        <!-- examples -->
                        <section class="color-section">
                            <h3>Usage Examples</h3>
                            <div class="usage-examples">
                                <div class="example-card" style="background: var(--p-surface-a); border: 1px solid var(--p-surface-border);">
                                    <h4 style="color: var(--p-primary-color);">Card with Primary Header</h4>
                                    <p style="color: var(--p-primary-color-text);">This is regular text content.</p>
                                    <p style="color: var(--p-text-secondary-color);">This is secondary text content.</p>
                                    <Button 
                                        label="Primary Button" 
                                        style="background: var(--p-primary-color); border-color: var(--p-primary-color);"
                                    />
                                </div>
                                
                                <div class="example-card" style="background: var(--p-surface-b); border: 1px solid var(--p-surface-border);">
                                    <h4 style="color: var(--p-text-color);">Surface B Background</h4>
                                    <div class="color-chips">
                                        <span class="chip" style="background: var(--p-green-500); color: white;">Success</span>
                                        <span class="chip" style="background: var(--p-orange-500); color: white;">Warning</span>
                                        <span class="chip" style="background: var(--p-blue-500); color: white;">Info</span>
                                        <span class="chip" style="background: var(--p-gray-500); color: white;">Neutral</span>
                                    </div>
                                </div>
                            </div>
                        </section>
                    </div>
                </template>
            </Card>
        </div>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue';
import Card from 'primevue/card';
import Button from 'primevue/button';
import type { IBeakerTheme } from '../plugins/theme';

const beakerApp = inject<any>("beakerAppConfig");
beakerApp?.setPage("playground");

const { theme, toggleDarkMode } = inject<IBeakerTheme>('theme');

const isDarkMode = computed(() => theme.mode === 'dark');

const toggleTheme = () => {
    toggleDarkMode();
};

const primaryColors = {
    'primary-color': 'Primary',
    'primary-50': '50',
    'primary-100': '100',
    'primary-200': '200',
    'primary-300': '300',
    'primary-400': '400',
    'primary-500': '500',
    'primary-600': '600',
    'primary-700': '700',
    'primary-800': '800',
    'primary-900': '900',
    'primary-950': '950',
};

const surfaceColors = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
    'border', 'ground', '0', '50', '100', '200', '300', '400', '500', 
    '600', '700', '800', '900', '950'
];

const textColors = [
    'text-color',
    'text-color-secondary', 
];

const semanticColors = {
    green: ['200', '300', '400', '500', '600', '700'],
    orange: ['200', '300', '400', '500', '600', '700'],
    blue: ['200', '300', '400', '500', '600', '700'],
    yellow: ['200', '300', '400', '500', '600', '700'],
    gray: ['200', '300', '400', '500', '600', '700'],
    slate: ['200', '300', '400', '500', '600', '700'],
};

const componentColors = [
    'content-background',
    'toolbar-background',
    'toolbar-border-color',
    'surface-border-radius',
];
</script>

<style lang="scss" scoped>
.playground-container {
    padding: 1rem;
    height: 100%;
    overflow-y: auto;
}

.theme-showcase {
    max-width: 100%;
    margin: 0 auto;
}

.showcase-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.color-sections {
    display: flex;
    flex-direction: column;
    gap: 2rem;
}

.color-section {
    h3 {
        color: var(--p-primary-color);
        margin-bottom: 1rem;
        border-bottom: 2px solid var(--p-surface-border);
        padding-bottom: 0.5rem;
    }
}

.color-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
}

.color-card {
    background: var(--p-surface-a);
    border: 1px solid var(--p-surface-border);
    border-radius: 8px;
    padding: 1rem;
    transition: all 0.2s ease;

    &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-color: var(--p-primary-color);
    }

    &.small {
        padding: 0.5rem;
        min-width: 120px;
    }
}

.color-swatch {
    width: 100%;
    height: 60px;
    border-radius: 6px;
    border: 1px solid var(--p-surface-border);
    margin-bottom: 0.5rem;
    
    &.small {
        height: 40px;
    }

    &.text-demo {
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.9rem;
    }
}

.color-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    &.small {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.25rem;
    }
}

.color-name {
    font-family: 'Courier New', monospace;
    font-size: 0.8rem;
    background: var(--p-surface-c);
    color: var(--p-text-color);
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    
    &.small {
        font-size: 0.7rem;
        padding: 0.1rem 0.3rem;
    }
}

.color-value {
    font-size: 1.5rem;
    font-weight: bold;
}

.semantic-colors {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.semantic-group {
    .semantic-title {
        color: var(--p-text-color);
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
    }
}

.color-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.usage-examples {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
}

.example-card {
    padding: 1.5rem;
    border-radius: 8px;
    
    h4 {
        margin-top: 0;
        margin-bottom: 1rem;
    }
    
    p {
        margin: 0.5rem 0;
    }
}

.color-chips {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-top: 1rem;
}

.chip {
    padding: 0.3rem 0.8rem;
    border-radius: 16px;
    font-size: 0.8rem;
    font-weight: 600;
}
</style> 