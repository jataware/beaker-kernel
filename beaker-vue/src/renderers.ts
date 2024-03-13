import { Component, VueElement, defineComponent, h } from 'vue';

import type { IBeakerRendererOptions, IMimeRenderer, MimetypeString } from 'beaker-kernel';
import { PartialJSONObject } from '@lumino/coreutils';
import VueJsonPretty from 'vue-json-pretty';
import katex from 'katex';

export interface BeakerRenderOutput {
    component: Component;
    bindMapping: {[key: string]: any};
}

export const JSONRenderer: IMimeRenderer<BeakerRenderOutput> = {
    rank: 60,
    mimetypes: ["application/json", "text/json"],
    render: (mimeType: MimetypeString, data: PartialJSONObject, metadata: PartialJSONObject) => {
        return {
            component: VueJsonPretty,
            bindMapping: {
                data: data,
                deep: "2",
                showLength: true,
                showIcon: true,
                showDoubleQuotes: "isQuotes",
                showLineNumber: "linenum",
            }
        };
    }
}

export const LatexRenderer: IMimeRenderer<BeakerRenderOutput> = {
    rank: 40,
    mimetypes: ["text/latex", "application/latex"],
    render: (mimeType: MimetypeString, data: PartialJSONObject, metadata: PartialJSONObject) => {
        const html = katex.renderToString(data.toString(), {
            displayMode: true,
            output: "mathml",
            throwOnError: false,
        });
        return {
            component: defineComponent(
                (props) => {
                    return () => {
                        return h('div', {innerHTML: props.html});
                    }
                    },
                    {
                    props: ["html"]
                    }
            ),
            bindMapping: {
                'html': html,
            }
        }
    }
}

export function wrapJupyterRenderer(jupyterRenderer: IMimeRenderer<HTMLElement>): IMimeRenderer<BeakerRenderOutput> {
    return {
        rank: jupyterRenderer.rank - 10,
        mimetypes: jupyterRenderer.mimetypes,
        render: (mimeType: MimetypeString, data: PartialJSONObject, metadata: PartialJSONObject) => {
            const rawHtmlElement: HTMLElement = jupyterRenderer.render(mimeType, data, metadata);
            return {
                component: defineComponent(
                    (props) => {
                        return () => {
                          return h('div', {innerHTML: props.html});
                        }
                      },
                      {
                        props: ["html"]
                      }
                ),
                bindMapping: {
                    'html': rawHtmlElement.outerHTML,
                }
            }

        }
    }
}