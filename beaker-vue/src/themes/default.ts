import { definePreset, palette } from '@primevue/themes';
import type { Preset, Theme, PaletteDesignToken } from '@primeuix/themes/types';
import Aura from '@primeuix/themes/aura';

function reversePallete(palleteObject: object) {
    console.log(palleteObject);
    const keys = Object.keys(palleteObject);
    const size = keys.length;
    const values = Object.values(palleteObject);

    const darkPallete = keys.map((key, idx) => [key, values[size - idx]])
    console.log({darkPallete});
    return Object.fromEntries(darkPallete);
}

const lightSurfacePalette: PaletteDesignToken = {
    ...palette('#708da9') as object,
    0: "#FFFFFF",
    50: "#808880",
};
const lightPrimaryPalette: PaletteDesignToken = {
    ...(palette('#7254f3') as object),
    0: "#5080AA",
    50: "#AA5080",
};
const darkSurfacePalette = {
    // ...reversePallete(palette('#a5a5a9') as object),
    // ...
    // 0: "#CCCCCC",
    // 50: "#BBBBBB",
    ...reversePallete(lightSurfacePalette),
};
// console.log(darkSurfacePalette);
// const lightSurfacePalette: PaletteDesignToken = {
// const lightPrimaryPalette: PaletteDesignToken = {
//     "0": "#FFF",
//     "50": "AFF",
//     "100": "#5FF",
//     "200": "#0FF",
// }
console.log({lightPrimaryPalette, lightSurfacePalette, darkSurfacePalette})


const BeakerTheme: Preset = definePreset(Aura, {
    semantic: {
        primary: lightPrimaryPalette,

        colorScheme: {
            light: {
                surface: lightSurfacePalette,
                // primary: lightPrimaryPalette,
                // mask: {
                //     background: "#999999",
                //     color: "#111111",
                // },
            },
            dark: {
                // surface: palette("#581144") as PaletteDesignToken,
                surface: darkSurfacePalette,
                // primary: {

                // },
                // content: {
                //     background: "#1c1b22"
                // },
            }
        },
    },
});

export default BeakerTheme;
