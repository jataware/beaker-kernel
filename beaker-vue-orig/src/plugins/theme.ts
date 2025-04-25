import { Plugin, App, reactive } from 'vue';

export declare type ThemeMode = "light" | "dark" | "default";

export declare interface IThemeConfig {
    name: string,
    lightTheme?: string, // Name of theme directory as exists in your public themes folder.
    darkTheme?: string, // Name of theme directory as exists in your public themes folder.
    defaultMode?: ThemeMode, // Default light/dark mode to use if not set.
    mode?: ThemeMode,  // Currently set light/dark mode value.
    overrides?: any, // css to override any defaults
    saveTheme?: boolean,
}

export declare interface IBeakerTheme {
    theme: IThemeConfig;
    setTheme: (name: string, mode: ThemeMode) => void;
    toggleDarkMode: () => void;
}

export const ThemeDefaults: IThemeConfig = {
    name: 'beaker-default',
    lightTheme: "beaker-light",
    darkTheme: "beaker-dark",
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
            const themeLink: HTMLLinkElement = document.querySelector('#primevue-theme');
            themeLink.addEventListener('error', (err) => {
                // Error loading the theme. Fallback to default.
                const failureCount = Number(localStorage.getItem('theme-failure-count')) || 0;
                Object.keys(ThemeDefaults).forEach((key) => {
                    theme[key] = ThemeDefaults[key];
                });
                // Clear theme from storage if it's a consistent problem.
                if (failureCount >= 5) {
                    localStorage.removeItem('theme');
                    localStorage.removeItem('theme-failure-count');
                }
                else {
                    localStorage.setItem('theme-failure-count', (failureCount+1).toString());
                }
                applyTheme()
            }, {once: true});
            themeLink.href = `/themes/${theme.mode === 'light'? theme.lightTheme : theme.darkTheme}/theme.css`;
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

        app.config.globalProperties.$beakerTheme = <IBeakerTheme>{
            theme,
            setTheme,
            toggleDarkMode,
        }
        app.provide('theme', app.config.globalProperties.$beakerTheme);
        applyTheme();
    },
}

export default BeakerThemePlugin;
