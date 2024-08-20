import { MimeModel, RenderMimeRegistry} from '@jupyterlab/rendermime';
import { Sanitizer } from '@jupyterlab/apputils';
import { standardRendererFactories, IRenderMime } from '@jupyterlab/rendermime';
import { PartialJSONObject } from '@lumino/coreutils';


export interface IBeakerRendererOptions {
    renderers: ReadonlyArray<IMimeRenderer>;
}

export type MimetypeString = "text/plain" | "text/html" | string;

/**
 *
 */
export interface IMimeBundle {
    [mimetype: MimetypeString]: PartialJSONObject;
}

export interface IMimeRenderer<OutputType = HTMLElement> {
    rank: number;
    mimetypes: MimetypeString[];
    render: (mimeType: MimetypeString, data: PartialJSONObject, metadata: PartialJSONObject) => OutputType;
}

export class MimeRenderer implements IMimeRenderer<HTMLElement> {

    public rank: number;
    public mimetypes: string[];

    public render(mimeType: MimetypeString, data: PartialJSONObject, metadata: PartialJSONObject): HTMLElement {

        return new HTMLElement();
    };

}

export class JupyterMimeRenderer extends MimeRenderer {

    constructor(factory: IRenderMime.IRendererFactory) {
        super();
        this._factory = factory
        this.rank = factory.defaultRank;
        this.mimetypes = [...factory.mimeTypes];
    }

    public render(mimeType: MimetypeString, data: PartialJSONObject, metadata?: PartialJSONObject): HTMLElement {
        const renderer = this._factory.createRenderer({
            mimeType,
            resolver: null,
            sanitizer: new Sanitizer(),
            linkHandler: null,
            latexTypesetter: null,
            markdownParser: null,
            translator: null,

        });
        const model = new MimeModel({
            trusted: true,
            data: {[mimeType]: data},
            metadata: metadata,
        });
        renderer.renderModel(model);
        return renderer.node;
    }
    private _factory: IRenderMime.IRendererFactory;
}

export class BeakerRenderer {

    constructor(options?: IBeakerRendererOptions) {
        this._renderers = {}
        for (const factory of standardRendererFactories) {
            const renderer = new JupyterMimeRenderer(factory);
            this.addRenderer(renderer);
        }
        for (const renderer of options?.renderers) {
            this.addRenderer(renderer);
        }
    }

    public addRenderer(renderer: IMimeRenderer) {
        for (const mimetype of renderer.mimetypes) {
            if (!Object.keys(this._renderers).includes(mimetype)) {
                this._renderers[mimetype] = renderer;
            }
            else {
                const prev_renderer = this._renderers[mimetype];
                if (renderer.rank <= prev_renderer.rank) {
                    this._renderers[mimetype] = renderer;
                }
            }
        }
    }

    public get rankedMimetypes(): MimetypeString[] {
        const mimetypes = Object.keys(this._renderers);
        mimetypes.sort((a, b) => this._renderers[a].rank - this._renderers[b].rank);
        return mimetypes;
    }

    public render(mimeType: MimetypeString, data: PartialJSONObject, metadata?: PartialJSONObject): any {
        const renderer = this._renderers[mimeType];
        if (renderer) {
            return renderer.render(mimeType, data, metadata);
        }
    }

    public renderMimeBundle(bundle: IMimeBundle, metadata?: PartialJSONObject): {[key: MimetypeString]: HTMLElement} {
        const result = {};
        for (const mimeType in bundle) {
            result[mimeType] = this.render(mimeType, bundle[mimeType], metadata)
        }
        return result;
    }

    public rankedMimetypesInBundle(bundle: IMimeBundle): MimetypeString[] {
        const result = this.rankedMimetypes.filter((mime) => bundle && Object.keys(bundle).includes(mime))
        return result;
    }

    private _renderers: {[key: string]: IMimeRenderer};
}
