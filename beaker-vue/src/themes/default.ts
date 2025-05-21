import { definePreset, palette } from '@primevue/themes';
import Aura from '@primeuix/themes/aura';

const lightSurfacePalette = palette('#708da9') as object;
const lightPrimaryPalette = palette('#7254f3') as object;
const darkSurfacePalette = palette('#a5a5a9') as object;

const BeakerTheme = definePreset(Aura, {
    semantic: {
        colorScheme: {
            light: {
                surface: lightSurfacePalette,
                primary: lightPrimaryPalette,
                mask: {
                    background: "#999999",
                    color: "#111111",
                },
            },
            dark: {
                surface: darkSurfacePalette,
            }
        }
    },
});

export default BeakerTheme;
