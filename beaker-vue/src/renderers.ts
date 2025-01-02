import { Component, VueElement, defineComponent, h } from 'vue';

import { IBeakerRendererOptions, IMimeRenderer, MimetypeString } from 'beaker-kernel/src';
import { PartialJSONObject } from '@lumino/coreutils';
import VueJsonPretty from 'vue-json-pretty';
import { marked } from 'marked';
import DecapodePreview from './components/render/DecapodePreview.vue';
import TablePreview from './components/render/TablePreview.vue';
import { MathJaxTypesetter } from '@jupyterlab/mathjax-extension'

const mathJaxTypsetter = new MathJaxTypesetter();
const mathJaxDocument = await mathJaxTypsetter.mathDocument();

export interface BeakerRenderOutput {
    component: Component;
    bindMapping: {[key: string]: any};
}

export const DecapodeRenderer: IMimeRenderer<BeakerRenderOutput> = {
    rank: 20,
    mimetypes: ["application/x-askem-decapode-json-graph"],
    render: (mimeType: MimetypeString, data: PartialJSONObject, metadata: PartialJSONObject) => {
        return {
            component: DecapodePreview,
            bindMapping: {
                data: data,
            },
        }
    }
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
                style: {
                    whiteSpace: "pre",
                },
            }
        };
    }
}

export const MarkdownRenderer: IMimeRenderer<BeakerRenderOutput> = {
    rank: 40,
    mimetypes: ["text/markdown", "text/x-markdown"],
    render: (mimeType: MimetypeString, data: PartialJSONObject, metadata: PartialJSONObject) => {
        const html = marked.parse(data.toString())
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
    },
}


export const LatexRenderer: IMimeRenderer<BeakerRenderOutput> = {
    rank: 40,
    mimetypes: ["text/latex", "application/latex"],
    render: (mimeType: MimetypeString, data: PartialJSONObject, metadata: PartialJSONObject) => {
        const input = data.toString();
        const output = mathJaxDocument.convert(input, {display: false}).outerHTML;
        return {
            component: defineComponent(
                (props) => {
                    return () => {
                        return h('div', {class: "beaker-latex", innerHTML: props.html, style: {fontSize: "1.5rem"}});
                    }
                    },
                    {
                        props: ["html"]
                    },
            ),
            bindMapping: {
                'html': output,
            }
        }
    }
}

export const TableRenderer: IMimeRenderer<BeakerRenderOutput> = {
    rank: 40,
    mimetypes: [
        "text/csv",
        "text/tsv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ],
    render: (mimeType: MimetypeString, data: PartialJSONObject, metadata: PartialJSONObject) => {
        return {
            component: TablePreview,
            bindMapping: {
                data: data,
                mimeType: mimeType
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
