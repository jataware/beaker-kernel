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
            // Allow default dark palette generation from light version.
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
        panel: {
            header: {
                borderRadius: `${dt('panel.root.borderRadius')} ${dt('panel.root.borderRadius')} 0 0`,
            },
            extend: {
                contentBorderRadius: `0 0 ${dt('panel.root.borderRadius')} ${dt('panel.root.borderRadius')}`,
            }
        },
        dialog: {
            extend: {
                "headerImage": "linear-gradient(45deg, var(--p-surface-a), var(--p-surface-a), var(--p-surface-a), var(--p-surface-b), var(--p-surface-b), var(--p-surface-b));",
            }
        },
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
    css: ({dt}) => `
:root {
    /* Define missing CSS custom properties for backward compatibility */
    --highlight-text-color: ${dt('primary.color')};
    --text-color: ${dt('text.color')};
    --text-color-secondary: ${dt('text.muted.color')};
}

/* Light mode specific variables */
:root:not(.beaker-dark) {
    --text-color-secondary: #6b7280; /* Gray-500 for better contrast in light mode */
}

/* Dark mode specific variables */
:root.beaker-dark {
    --text-color-secondary: #9ca3af; /* Gray-400 for better contrast in dark mode */
}

.p-panel-content {
    border-radius: ${dt('panel.contentBorderRadius')};
}

.p-dialog-header {
    background-image: ${dt('dialog.headerImage')};
    border-top-left-radius: inherit;
    border-top-right-radius: inherit;
}

.p-dialog-footer {
    border-bottom-left-radius: inherit;
    border-bottom-right-radius: inherit;
}
    `,
});

export default BeakerTheme;
