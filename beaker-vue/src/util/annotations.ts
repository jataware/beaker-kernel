import type { Extension } from "@codemirror/state";
import { EditorView, Decoration, type DecorationSet, hoverTooltip } from "@codemirror/view";
import { linter, lintGutter, type Diagnostic } from "@codemirror/lint";
import { StateField, StateEffect } from "@codemirror/state";

export interface AnnotationData {
    cell_id: string;
    issue: {
        id: string;
        title: string;
        description: string;
        prompt_description?: string | null;
        severity: "error" | "warning" | "info";
        link?: string | null;
        category?: {
            id: string;
            display_label: string;
            color: string;
            icon?: string | null;
        } | null;
    };
    start: number;
    end: number;
    title_override?: string | null;
    message_override?: string | null;
    message_extra?: string | null;
    link?: string;
}

export interface AnnotationProvider {
    name: string;
    createExtensions(annotations: AnnotationData[]): Extension[];
}

export class LinterAnnotationProvider implements AnnotationProvider {
    name = "linter";

    createExtensions(annotations: AnnotationData[]): Extension[] {
        if (!annotations?.length) return [];

        const linterAnnotations = linter((view: EditorView) => {
            return annotations.map(annotation => {
                const category_id = annotation.issue.category?.id ?? "default";
                const className = `category-${category_id} icon-${annotation.issue.category?.icon ?? "default"}`;
                const diagnostic: Diagnostic = {
                    from: annotation.start,
                    to: annotation.end,
                    severity: annotation.issue.severity,
                    message: annotation.title_override ?? annotation.issue.title,
                    markClass: className,
                    source: category_id,
                    renderMessage() {
                        const el = document.createElement('div');
                        const description = annotation.message_override || annotation.issue.description;
                        const extraMessage = annotation.message_extra ? `<p>${annotation.message_extra}</p>` : '';
                        el.innerHTML = `<h4 style="margin: 0.2rem 0">${annotation.title_override || annotation.issue.title}</h4>`;
                        el.innerHTML += `<p>${description}</p>`;
                        if(extraMessage) {
                            el.innerHTML += `<p>${extraMessage}</p>`;
                        }
                        return el;
                    },
                };
                
                if (annotation.link) {
                    diagnostic.actions = [{
                        name: "Learn More",
                        apply: () => window.open(annotation.link, '_blank')
                    }];
                }
                
                return diagnostic;
            });
        });

        return [
            linterAnnotations,
            lintGutter({
                hoverTime: 200,
            })
        ];
    }
}

export class DecorationAnnotationProvider implements AnnotationProvider {
    name = "decoration";

    createExtensions(annotations: AnnotationData[]): Extension[] {
        if (!annotations?.length) return [];

        const buildDecorations = (annotations: AnnotationData[]): DecorationSet => {
            const decorations = annotations.map(annotation => {
                const category_id = annotation.issue.category?.id ?? "default";
                const className = `annotation-mark category-${category_id}`;
                
                return Decoration.mark({
                    class: className,
                    attributes: {
                        'data-annotation-id': annotation.issue.id,
                        'data-category': category_id,
                        'data-severity': annotation.issue.severity,
                        'title': annotation.title_override ?? annotation.issue.title
                    }
                }).range(annotation.start, annotation.end);
            });

            return Decoration.set(decorations, true);
        };

        const updateDecorations = StateEffect.define<AnnotationData[]>();

        const decorationField = StateField.define<DecorationSet>({
            create() {
                return buildDecorations(annotations);
            },
            update(decorations, tr) {
                for (let effect of tr.effects) {
                    if (effect.is(updateDecorations)) {
                        return buildDecorations(effect.value);
                    }
                }
                return decorations.map(tr.changes);
            },

            provide: f => EditorView.decorations.from(f)
        });

        const decorationTheme = EditorView.theme({
            '.annotation-mark': {
                textDecoration: 'underline wavy',
                textDecorationSkipInk: 'none',
                cursor: 'help'
            },
            '.annotation-mark.category-literal': {
                '--color': '#FFFF00',
                backgroundColor: 'color-mix(in srgb, var(--color) 20%, transparent)',
                textDecorationColor: 'rgba(255, 255, 0, 0.5)'
            },
            '.annotation-mark.category-assumptions': {
                backgroundColor: 'rgba(255, 204, 34, 0.1)',
                textDecorationColor: 'rgba(255, 204, 34, 0.5)'
            },
            '.annotation-mark.category-grounding': {
                backgroundColor: 'rgba(255, 0, 0, 0.1)',
                textDecorationColor: 'rgba(255, 0, 0, 0.5)'
            },
            '.annotation-mark.category-grounding.category-literal': {
                backgroundColor: 'rgba(0, 255, 0, 0.1)',
                textDecorationColor: 'rgba(0, 255, 0, 0.5)'
            }
        });

        const annotationTooltip = hoverTooltip((view, pos, side) => {
            console.log('Hover tooltip triggered at position:', pos);
            
            const decorations = view.state.field(decorationField);
            let foundAnnotation: AnnotationData | null = null;

            decorations.between(pos, pos, (from, to, value) => {
                const annotationId = value.spec.attributes?.['data-annotation-id'];
                
                if (annotationId) {
                    foundAnnotation = annotations.find(a => a.issue.id === annotationId) || null;
                    console.log('Found annotation:', foundAnnotation);
                }
            });

            if (!foundAnnotation) {
                console.log('No annotation found at position');
                return null;
            }

            console.log('Creating tooltip for annotation:', foundAnnotation);

            return {
                pos,
                above: true,
                create(view) {
                    const dom = document.createElement('div');
                    dom.className = 'annotation-tooltip';
                    
                    const description = foundAnnotation!.message_override || foundAnnotation!.issue.description;
                    const extraMessage = foundAnnotation!.message_extra ? `<p>${foundAnnotation!.message_extra}</p>` : '';
                    
                    dom.innerHTML = `
                        <h4 style="margin: 0.2rem 0; color: var(--p-text-color)">${foundAnnotation!.title_override || foundAnnotation!.issue.title}</h4>
                        <p style="color: var(--p-text-color)">${description}</p>
                        ${extraMessage}
                    `;

                    if (foundAnnotation!.link) {
                        const link = document.createElement('a');
                        link.href = foundAnnotation!.link;
                        link.target = '_blank';
                        link.textContent = 'Learn More';
                        link.style.cssText = 'display: inline-block; margin-top: 0.5rem; color: var(--p-primary-color);';
                        dom.appendChild(link);
                    }

                    console.log('Created tooltip DOM:', dom);
                    return { dom };
                }
            };
        });

        return [decorationField, decorationTheme, annotationTooltip];
    }
}

export class AnnotationProviderFactory {
    private static providers = new Map<string, () => AnnotationProvider>([
        ['linter', () => new LinterAnnotationProvider()],
        ['decoration', () => new DecorationAnnotationProvider()],
    ]);

    static register(name: string, factory: () => AnnotationProvider): void {
        this.providers.set(name, factory);
    }

    static create(type: string): AnnotationProvider {
        const factory = this.providers.get(type);
        if (!factory) {
            throw new Error(`Unknown annotation provider type: ${type}`);
        }
        return factory();
    }

    static getAvailableTypes(): string[] {
        return Array.from(this.providers.keys());
    }
} 