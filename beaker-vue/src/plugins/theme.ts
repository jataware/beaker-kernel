import { Plugin, App, reactive } from 'vue';

export declare type ThemeMode = "light" | "dark" | "default";

export declare interface IThemeConfig {
    name: string,
    lightTheme?: string, // Name of theme directory as exists in your public themes folder.
    darkTheme?: string, // Name of theme directory as exists in your public themes folder.
    mode?: ThemeMode,
    overrides?: any, // css to override any defaults
    saveTheme?: boolean,
}

export const ThemeDefaults: IThemeConfig = {
    name: 'soho',
    lightTheme: "soho-light",
    darkTheme: "soho-dark",
    mode: 'light',
    saveTheme: true,
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
            }
        }
        theme = reactive(theme);


        const applyTheme = () => {
            const themeLink: HTMLLinkElement = document.querySelector('#primevue-theme');
            themeLink.href = `/themes/${theme.mode === 'light'? theme.lightTheme : theme.darkTheme}/theme.css`;
        };

        const toggleDarkMode = () => {
            theme.mode = theme.mode === 'light' ? 'dark' : 'light'
            if (theme.saveTheme) {
                localStorage.setItem('theme', JSON.stringify(theme));
            }
            applyTheme();
        };

        const setTheme = (name: string, mode: ThemeMode) => {
            theme.name = name;
            theme.mode = mode;
            if (theme.saveTheme) {
                localStorage.setItem('theme', JSON.stringify(theme));
            }
            applyTheme();
        };

        app.config.globalProperties.$beakerTheme = {
            theme,
            setTheme,
            toggleDarkMode,
        }
        app.provide('theme', app.config.globalProperties.$beakerTheme);
        applyTheme();
    },
}

export default BeakerThemePlugin;
