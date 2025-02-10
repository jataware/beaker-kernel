import { Plugin, App, reactive, Component, computed,  } from 'vue';

// import { _, getAsset, hasAsset, hasTemplateValue, Asset } from '../util/whitelabel';

export interface Asset {
    slug: string;
    src: string;
    attrs: {
        [key: string]: string;
    };
}


declare module 'vue' {
    interface ComponentCustomProperties {
        $tmpl: {
            _: (templateName: string, defaultValue?: string) => string,
            hasTemplateValue: (templateName: string) => boolean,
            getAsset: (assetName: string) => Asset,
            hasAsset: (assetName: string) => boolean,
        }
    }
}

export const BeakerAppConfigPlugin: Plugin = {
    install(app: App, beakerAppConfig?: any) {
        if (!beakerAppConfig) {
            // Fetch app config from globally defined instance or create fresh, empty version.
            beakerAppConfig = global['beaker_app'] || {};
        }
        const templateValues = beakerAppConfig.templateStrings || {};
        const assetValues = beakerAppConfig.assets || {};

        const _ = (templateName: string, defaultValue?: string): string => {
            if (templateName in templateValues) {
                const template: string = templateValues[templateName];

                return template
            }
            else {
                return defaultValue ? defaultValue : '';
            }
        }

        function hasTemplateValue(templateName: string): boolean {
            return templateName in templateValues;
        }

        function hasAsset(assetName: string): boolean {
            return assetName in assetValues;
        }

        function getAsset(assetName: string): Asset {
            if (assetName in assetValues) {
                return assetValues[assetName];
            }
            else {
                return undefined;
            }
        }

        app.config.globalProperties.$tmpl = {
            _,
            getAsset,
            hasAsset,
            hasTemplateValue
        };

        const setPage = (page: string) => {
            console.log({beakerAppConfig});
            setPageTitle(page)
            const globalStyle = beakerAppConfig?.stylesheet;
            const pageStyle = beakerAppConfig?.pages?.[page]?.stylesheet;
            if (globalStyle) {
                setStylesheet(globalStyle, "beakerapp-global");
            }
            if (pageStyle) {
                setStylesheet(pageStyle, "beakerapp-page");
            }
        }

        const setStylesheet = (stylesheet: string | {[key: string]: string}, id: string) => {
            console.log("setting stylesheet ", stylesheet);
            if (typeof(stylesheet) === "string") { // URL
                const linkElement = document.getElementById(id) || document.createElement("link");
                linkElement.setAttribute("href", stylesheet);
                linkElement.setAttribute("rel", "stylesheet");
                linkElement.setAttribute("id", id);
                document.head.appendChild(linkElement);
            }
        }

        const setPageTitle = (page: string) => {
            console.log("settingPageTitle for ", page);
            const pageConfig = beakerAppConfig?.pages?.[page];
            if (pageConfig?.title) {
                document.title = pageConfig.title;
            }

        }

        app.config.globalProperties.$beakerAppConfig = <any>{
            config: beakerAppConfig,
            setPageTitle,
            setPage,
        }
        app.provide('beakerAppConfig', app.config.globalProperties.$beakerAppConfig);
    },
}

export default BeakerAppConfigPlugin;
