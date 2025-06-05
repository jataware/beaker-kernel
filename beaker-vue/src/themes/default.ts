import { definePreset, palette, shade, tint, mix, dt } from '@primevue/themes';
import type { Preset, Theme, PaletteDesignToken } from '@primeuix/themes/types';
import Aura from '@primeuix/themes/aura';
import { makePalette } from './util';

const primarySurfaceColor = '#708da9';

const lightSurfacePalette: PaletteDesignToken = makePalette(primarySurfaceColor, 7, 95);
const lightPrimaryPalette: PaletteDesignToken = makePalette("#7254f3");

const BeakerTheme: Preset = definePreset(Aura, {
    semantic: {
        primary: lightPrimaryPalette,
        colorScheme: {
            light: {
                surface: <PaletteDesignToken>{
                    ...lightSurfacePalette,
                    border: dt('surface.200'),
                    a: dt('surface.0'),
                    b: dt('surface.50'),
                    c: dt('surface.100'),
                    d: dt('surface.200'),
                    e: dt('surface.300'),
                    f: dt('surface.400'),
                    g: dt('surface.500'),
                    h: dt('surface.600'),
                    i: dt('surface.700'),
                    j: dt('surface.800'),
                    k: dt('surface.900'),
                    l: dt('surface.950'),
                }

            },
            // Allow defualt dark palette generation from light version.
            dark: {
                surface: <PaletteDesignToken>{
                    ...lightSurfacePalette,
                    border: dt('surface.800'),
                    a: dt('surface.950'),
                    b: dt('surface.900'),
                    c: dt('surface.800'),
                    d: dt('surface.700'),
                    e: dt('surface.600'),
                    f: dt('surface.500'),
                    g: dt('surface.400'),
                    h: dt('surface.300'),
                    i: dt('surface.200'),
                    j: dt('surface.100'),
                    k: dt('surface.50'),
                    l: dt('surface.0'),
                },
            }
        },
    },
    components: {
        toolbar: {
            root: {
                background: 'var(--p-surface-b)',
            }
        },
        menubar: {
            root: {
                background: 'var(--p-surface-b)',
            }
        },
        datatable: {
            headerCell: {
                background: 'var(--p-surface-b)',
            }
        },
    },
    extend: {
        surface: {
            borderRadius: "6px",
        },
        tree: {
            borderColor: `solid 1px ${dt('content.border.color')}`,
        },
    },
});

export default BeakerTheme;
