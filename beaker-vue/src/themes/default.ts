import { definePreset, palette, dt } from '@primevue/themes';
import type { Preset, Theme, PaletteDesignToken } from '@primeuix/themes/types';
import Aura from '@primeuix/themes/aura';

const lightSurfacePalette: PaletteDesignToken = {
    ...palette('#708da9') as object,
    0: "#ffffff",
};
const lightPrimaryPalette: PaletteDesignToken = {
    ...(palette('#7254f3') as object),
    0: "#5080AA",
};

const BeakerTheme: Preset = definePreset(Aura, {
    primitive: <Object>{
        bluegrey: palette("#6878a0"),
    },
    semantic: {
        primary: lightPrimaryPalette,
        colorScheme: {
            light: {
                surface: lightSurfacePalette,
            },
        },
    },
    components: {
        toolbar: {
            root: {
                background: 'var(--surface-b)',
            }
        },
        menubar: {
            root: {
                background: 'var(--surface-b)',
            }
        },
        datatable: {
            headerCell: {
                background: 'var(--surface-b)',
            }
        }

    },
    extend: {
        surface: {
            border: "#dfe7ef",
            borderRadius: "6px",
        },
        tree: {
            borderColor: dt('content.border.color'),
        },
    },
//     css: ({ dt }) => `
// :root {
//     --foo: ${dt('content.background')};
//     --foo-a: ${dt('content.border.color')};
//     --foo-b: ${dt('content.border')};
// }
// .p-tree {
//     border: ${dt('content.border.width')} solid ${dt('content.border.color')};
//     border-radius: ${dt('surface.borderRadius')}
// }
//     `,
});


console.log({Aura});

export default BeakerTheme;
