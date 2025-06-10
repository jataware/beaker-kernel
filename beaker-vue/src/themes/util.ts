import { shade, tint } from '@primevue/themes';
import type { PaletteDesignToken } from '@primeuix/themes/types';

export const paletteKeys = [0, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950];

export const makePalette = (color: string, lowerBound: number = 0, upperBound: number = 100): PaletteDesignToken => {
    return Object.fromEntries(
        paletteKeys.map(key => {
            var action: (color: string, amount: number) => string, amount: number;
            const distancePct = (500 - key) / 500;
            const distanceRaw = (upperBound - lowerBound) * distancePct;
            const distance = distanceRaw < 0 ? distanceRaw - lowerBound : distanceRaw + lowerBound;
            if (distance >= 0) {
                action = tint;
                amount = distance;
            }
            else {
                action = shade;
                amount = -distance;
            }
            const finalColor = action(color, amount);
            return [key, finalColor]
        })
    )
}
