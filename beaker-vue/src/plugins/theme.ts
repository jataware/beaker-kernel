import { reactive } from 'vue';
import type { Plugin, App } from 'vue';

export declare type ThemeMode = "light" | "dark" | "default";

export declare interface IThemeConfig {
    name: string,
    path?: string,
    defaultMode?: ThemeMode, // Default light/dark mode to use if not set.
    mode?: ThemeMode,  // Currently set light/dark mode value.
    saveTheme?: boolean,
}

export declare interface IBeakerTheme {
    theme: IThemeConfig;
    setTheme: (path: string, mode: ThemeMode) => void;
    toggleDarkMode: () => void;
    setDarkMode: () => void;
}

export const ThemeDefaults: IThemeConfig = {
    name: 'beaker-default',
    // path: '@/themes/default',
    defaultMode: 'light',
    saveTheme: false,
}

export const BeakerThemePlugin: Plugin = {
    install(app: App, theme?: IThemeConfig) {
        if (theme === undefined) {
            theme = ThemeDefaults;
        }
        else {
            theme = {...ThemeDefaults, ...theme};
        }
        const savedThemeString = localStorage.getItem("theme");
        if (savedThemeString !== null) {
            try {
                const savedTheme = JSON.parse(savedThemeString);
                // Update theme, with savedTheme second to take precedence.
                theme = {...theme, ...savedTheme};
            }
            catch (e) {
                console.error("Error when trying to parse saved them json string.", e);
                theme = {...ThemeDefaults};
                localStorage.setItem('theme', JSON.stringify(theme));
            }
        }
        theme.mode = <ThemeMode>localStorage.getItem('theme-lightmode') || theme.defaultMode || 'light';
        theme = reactive(theme);

        const applyTheme = () => {

            const appElement = document.documentElement;
            if (theme.mode === 'light' || theme.mode === 'default') {
                appElement.classList.remove('beaker-dark');
            }
            else {
                appElement.classList.add('beaker-dark');
            }
        };

        const toggleDarkMode = () => {
            theme.mode = theme.mode === 'light' ? 'dark' : 'light'
            if (theme.saveTheme) {
                localStorage.setItem('theme', JSON.stringify(theme));
            }
            localStorage.setItem('theme-lightmode', theme.mode);
            applyTheme();
        };

        const setTheme = (name: string, mode: ThemeMode) => {
            theme.name = name;
            theme.mode = mode;
            if (theme.saveTheme) {
                localStorage.setItem('theme', JSON.stringify(theme));
            }
            localStorage.setItem('theme-lightmode', theme.mode);
            applyTheme();
        };

        const setDarkMode = (mode) => {
            theme.mode = mode || theme.defaultMode;
            if (theme.saveTheme) {
                localStorage.setItem('theme', JSON.stringify(theme));
            }
            localStorage.setItem('theme-lightmode', theme.mode);
            applyTheme();
        }

        app.config.globalProperties.$beakerTheme = <IBeakerTheme>{
            theme,
            setTheme,
            toggleDarkMode,
            setDarkMode,
        }
        app.provide('theme', app.config.globalProperties.$beakerTheme);
        applyTheme();
    },
}

export default BeakerThemePlugin;
