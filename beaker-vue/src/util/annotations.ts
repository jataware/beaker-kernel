import type { Extension } from "@codemirror/state";
import { EditorView, Decoration, type DecorationSet, hoverTooltip, gutter, GutterMarker } from "@codemirror/view";
import { linter, lintGutter, type Diagnostic } from "@codemirror/lint";
import { StateField, StateEffect, RangeSet } from "@codemirror/state";


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

function getSeverityColor(severity: string): string {
    switch (severity) {
        case 'error': return '#e74c3c';
        case 'warning': return '#f39c12';
        case 'info': return '#3498db';
        default: return '#95a5a6';
    }
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

        const getAnnotationsByLine = (annotations: AnnotationData[], doc: any) => {
            const lineAnnotations = new Map<number, AnnotationData[]>();
            
            annotations.forEach(annotation => {
                const line = doc.lineAt(annotation.start);
                const lineNumber = line.number;
                
                if (!lineAnnotations.has(lineNumber)) {
                    lineAnnotations.set(lineNumber, []);
                }
                lineAnnotations.get(lineNumber)!.push(annotation);
            });
            
            return lineAnnotations;
        };

        const getUniqueSeverities = (annotations: AnnotationData[]): string[] => {
            const severities = new Set(annotations.map(a => a.issue.severity));
            const ordered = ['error', 'warning', 'info'].filter(s => severities.has(s));
            return ordered;
        };

        class SeverityGutterMarker extends GutterMarker {
            constructor(private severities: string[]) {
                super();
            }

            eq(other: SeverityGutterMarker) {
                return this.severities.length === other.severities.length &&
                       this.severities.every((s, i) => s === other.severities[i]);
            }

            toDOM() {
                const container = document.createElement('div');
                container.className = 'annotation-gutter-markers';
                container.style.cssText = `
                    display: flex;
                    justify-content: flex-end;
                    padding-right: -1px;
                    padding-top: 1px;
                    height: 1.6rem;
               `;

                this.severities.forEach((severity, index) => {
                    const line = document.createElement('div');
                    line.className = `annotation-gutter-line severity-${severity}`;
                    line.style.cssText = `
                        width: 5px;
                        height: 1.3rem;
                        align-self: flex-start;
                        border-radius: 1px;
                        background-color: ${this.getSeverityColor(severity)};
                    `;
                    container.appendChild(line);
                });

                return container;
            }

            public getSeverityColor = getSeverityColor;
        }

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
                        // 'title': annotation.title_override ?? annotation.issue.title
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

        const gutterMarkerField = StateField.define<RangeSet<GutterMarker>>({
            create(state) {
                const lineAnnotations = getAnnotationsByLine(annotations, state.doc);
                const markers = [];

                for (const [lineNumber, lineAnns] of lineAnnotations) {
                    const severities = getUniqueSeverities(lineAnns);
                    if (severities.length > 0) {
                        const line = state.doc.line(lineNumber);
                        markers.push(new SeverityGutterMarker(severities).range(line.from));
                    }
                }

                return RangeSet.of(markers, true);
            },
            update(markers, tr) {
                return markers.map(tr.changes);
            }
        });

        const annotationGutter = gutter({
            class: "annotation-gutter",
            markers: view => view.state.field(gutterMarkerField)
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
            },
            '.annotation-gutter': {
                width: '1.2em',
                display: 'flex',
                alignItems: 'center'
            },
            '.annotation-gutter-markers': {
                width: '100%',
                height: '100%'
            }
        });

        const annotationTooltip = hoverTooltip((view, pos, side) => {
            console.log('hover tooltip triggered at pos:', pos);
            
            const decorations = view.state.field(decorationField);
            let foundAnnotations: AnnotationData[] = [];

            decorations.between(pos, pos, (from, to, value) => {
                console.log('decoration between', from, to, value);
                const annotationId = value.spec.attributes?.['data-annotation-id'];
                console.log('annotation ID from decoration:', annotationId);
                
                if (annotationId) {
                    const annotation = annotations.find(a => a.issue.id === annotationId);
                    if (annotation) {
                        foundAnnotations.push(annotation);
                    }
                }
            });

            if (foundAnnotations.length === 0) {
                console.log('no annotations found position');
                return null;
            }

            console.log('creating tooltip for annotations:', foundAnnotations);

            return {
                pos,
                above: true,
                create(view) {
                    const dom = document.createElement('div');
                    dom.className = 'annotation-tooltip';
                    
                    foundAnnotations.forEach((annotation, index) => {
                        if (index > 0) {
                            const separator = document.createElement('hr');
                            separator.style.cssText = 'margin: 1rem 0; border: none; border-top: 1px solid var(--p-surface-border);';
                            dom.appendChild(separator);
                        }

                        const section = document.createElement('div');
                        const description = annotation.message_override || annotation.issue.description;
                        const extraMessage = annotation.message_extra ? `<p>${annotation.message_extra}</p>` : '';
                        
                        section.innerHTML = `
                            <h4 style="margin: 0.2rem 0; color: var(--p-text-color)">
                            <span style="color: ${getSeverityColor(annotation.issue.severity)}">${annotation.issue.severity}</span> ${annotation.title_override || annotation.issue.title}
                            </h4>
                            <p style="color: var(--p-text-color)">${description}</p>
                            ${extraMessage}
                        `;

                        if (annotation.link) {
                            const link = document.createElement('a');
                            link.href = annotation.link;
                            link.target = '_blank';
                            link.textContent = 'Learn More';
                            link.style.cssText = 'display: inline-block; margin-top: 0.5rem; color: var(--p-primary-color);';
                            section.appendChild(link);
                        }

                        dom.appendChild(section);
                    });

                    console.log('created tooltip DOM:', dom);
                    return { dom };
                }
            };
        });

        return [decorationField, gutterMarkerField, annotationGutter, decorationTheme, annotationTooltip];
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