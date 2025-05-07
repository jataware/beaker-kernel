<template>
    <BaseInterface
        :title="$tmpl._('short_title', 'Playground')"
        ref="beakerInterfaceRef"
        :header-nav="headerNav"
        :connectionSettings="props.config"
        sessionName="playground_interface"
        :sessionId="sessionId"
        defaultKernel="beaker_kernel"
    >
        <div class="chat-layout">
        <h3 style="margin-left: 1rem;">Hello, World</h3>

        <Codemirror
            :extensions="extensions"
            v-model="model"
            @ready="handleReady"
        />
        </div>
    </BaseInterface>
</template>

<script setup lang="ts">
import BaseInterface from './BaseInterface.vue';

import NotebookSvg from '../assets/icon-components/NotebookSvg.vue';

import { NavOption } from '../components/misc/BeakerHeader.vue';

import { defineProps, inject, ref, computed, ComponentInstance, Component, StyleHTMLAttributes, ComputedRef, shallowRef } from 'vue';

import { IBeakerTheme } from '../plugins/theme';

import { Codemirror } from "vue-codemirror";
import { EditorView, keymap } from "@codemirror/view";
import { EditorState, Extension, Prec } from "@codemirror/state";
import { oneDark } from "@codemirror/theme-one-dark";
import { LanguageSupport } from "@codemirror/language";
import { autocompletion, completionKeymap, completionStatus, selectedCompletion, acceptCompletion, closeCompletion, startCompletion } from "@codemirror/autocomplete";
import { BeakerLanguage, LanguageRegistry, getCompletions } from "../util/autocomplete";
import { BeakerSession } from 'beaker-kernel/src';
import { linter, Diagnostic, lintGutter } from "@codemirror/lint";
import sampleCodeText from "../assets/sample_code_aqs.txt?raw";

const beakerInterfaceRef = ref();
const { theme, toggleDarkMode } = inject<IBeakerTheme>('theme');
const beakerApp = inject<any>("beakerAppConfig");
beakerApp.setPage("playground");

const ANNOTATION_TYPES = {
    logic_error: {
        "id": "logic_error",
        "display": "Potential Logical Error",
        "color": "#FF0012",
        "message_table": {
            "fallacy_1": {
                "title": "You made a boo-boo!",
                "description": "Here's why you're so dumb!",
                "severity": "major",
                "link": "https://lmgtfy.com/"
            },
            "average_of_averages": {
                "title": "Potential averaging of averages",
                "description": "Potential averaging of a list of averages",
                "severity": "warning",
                "link": "https://wikipedia.org/wiki/Common_errors_in_statistical_analysis"
                }
            }
    },
    assumptions: {
        "id": "assumptions",
        "display": "Assumptions in code",
        "color": "#AA8888",
        "severity": "info",
        "message_table": {
            "assumption_in_algorithm": {
                "title": "Assumption in algorithm",
                "description": "The following assumption was made in this algorithm:\n",
                "link": "https://lmgtfy.com/"
            },
            "assumption_in_value": {
                "title": "Assumption in value",
                "description": "The following assumption was made with regards to the value of this variable:\n",
                "link": "https://lmgtfy.com/"
            }
        }
    }
}

const MOCK_ANNOTATIONS = [
    {
        "start": 0,  // Character, not line
        "end": 19,
        "error_type": "logic_error",
        "error_id": "fallacy_1",
        // "title_override": "",
        // "message_override": "",
        "message_extra": "", 
    },
    {
        "start": 138,  // Character, not line
        "end": 181,
        "error_type": "assumptions",
        "error_id": "assumption_in_value",
        "message_extra": "Value is assumed to always be positive.", 
    }
]

// const createDiagnosticFromAnnotation = (annotation: typeof MOCK_ANNOTATIONS[0]): Diagnostic => {
//   const annotationType = ANNOTATION_TYPES[annotation.error_type];
//   const messageInfo = annotation.error_id ? 
//     annotationType.message_table[annotation.error_id] : 
//     null;

//   return {
//     from: annotation.start,
//     to: annotation.end,
//     severity: messageInfo?.severity || "info",
//     message: annotation.message_override || messageInfo?.title || annotationType.display,
//     actions: messageInfo?.link ? [{
//       name: "Learn More",
//       apply: () => window.open(messageInfo.link, '_blank')
//     }] : undefined
//   }
// }


const sampleCode = ref(sampleCodeText);
const model = ref<string>(sampleCode.value);

const codeMirrorView = shallowRef<EditorView>();
const codeMirrorState = shallowRef();

interface CodeHighlight {
    from: number;
    to: number;
    message: string;
}

// const currentHighlights = ref<CodeHighlight[]>([]);
// const addHighlightEffect = StateEffect.define<CodeHighlight[]>();

// const createErrorDecoration = (message: string) => Decoration.mark({
//     class: "cm-error-highlight",
//     attributes: { title: message }
// });
// const highlightField = StateField.define<DecorationSet>({
//     create() {
//         return Decoration.none;
//     },
//     update(highlights, tr) {
//         // map decorations through document changes
//         highlights = highlights.map(tr.changes);
        
//         // apply any highlight effects from the transaction
//         for (let e of tr.effects) {
//             if (e.is(addHighlightEffect)) {
//                 const decorations = e.value.map(highlight => 
//                     createErrorDecoration(highlight.message).range(highlight.from, highlight.to)
//                 );
//                 highlights = Decoration.set(decorations, true);
//             }
//         }
        
//         return highlights;
//     }
// });

// const addHighlight = (view: EditorView, from: number, to: number, message: string) => {
//     currentHighlights.value.push({ from, to, message });
    
//     view.dispatch({
//         effects: addHighlightEffect.of(currentHighlights.value)
//     });
// };

const handleReady = ({view, state}) => {
    codeMirrorView.value = view;
    codeMirrorState.value = state;
    // currentHighlights.value = [];
    
    // NOTE helper for mocks to find position of text, although our engine
    // will just provide the from/to without specifying the text
    // const findPositionInDoc = (searchText: string): { from: number, to: number } | null => {
    //     const doc = view.state.doc.toString();
    //     const from = doc.indexOf(searchText);
    //     if (from === -1) return null;
    //     return {
    //         from,
    //         to: from + searchText.length
    //     };
    // };
    
    // add mock highlights
    // setTimeout(() => {

    //     const pos1 = {from: 10, to: 22};
    //     if (pos1) {
    //         addHighlight(
    //             view,
    //             pos1.from,
    //             pos1.to,
    //             "Type error: Cannot concatenate string with numbers"
    //         );
    //     }
        
    //     const pos2 = {from: 59, to: 85};
    //     if (pos2) {
    //         addHighlight(
    //             view,
    //             pos2.from,
    //             pos2.to,
    //             "Reference error: undefined_variable is not defined"
    //         );
    //     }
    // }, 200);
};

const session: BeakerSession = inject('session');

const headerNav = computed((): NavOption[] => {
    const nav: NavOption[] = [
        {
            type: 'button',
            command: () => {
                console.log("Reset Session");
            },
            icon: 'refresh',
            label: 'Reset Session',
        }

    ];
    if (!(beakerApp?.config?.pages) || (Object.hasOwn(beakerApp.config.pages, "notebook"))) {
        const href = "/" + (beakerApp?.config?.pages?.notebook?.default ? '' : 'notebook') + window.location.search;
        nav.push(
            {
                type: 'link',
                href: href,
                component: NotebookSvg,
                componentStyle: {
                    fill: 'currentColor',
                    stroke: 'currentColor',
                    height: '1rem',
                    width: '1rem',
                },
                label: 'Navigate to notebook view',
            }
        );
    }
    nav.push(...([
        {
            type: 'button',
            icon: (theme.mode === 'dark' ? 'sun' : 'moon'),
            command: toggleDarkMode,
            label: `Switch to ${theme.mode === 'dark' ? 'light' : 'dark'} mode.`,
        },
        {
            type: 'link',
            href: `https://jataware.github.io/beaker-kernel`,
            label: 'Beaker Documentation',
            icon: "book",
            rel: "noopener",
            target: "_blank",
        },
        {
            type: 'link',
            href: `https://github.com/jataware/beaker-kernel`,
            label: 'Check us out on Github',
            icon: "github",
            rel: "noopener",
            target: "_blank",
        }
    ] as NavOption[]));
    return nav;
});

const urlParams = new URLSearchParams(window.location.search);

const sessionId = urlParams.has("session") ? urlParams.get("session") : "playground_dev_session";

const props = defineProps([
    "config",
    "connectionSettings",
    "renderers",
]);

const extensions = computed(() => {
    const filteredCompletionKeymap = completionKeymap.filter(item => !['Tab', 'Escape'].includes(item.key));
    const overriddenKeymap = [
        ...filteredCompletionKeymap,
        {key: "Tab", run: (editorView: EditorView) => {
            const editorState = editorView.state;
            const selection = editorState.selection.main;

            const startLine = editorState.doc.lineAt(selection.from);
            const firstNonWhitespaceOffset = startLine.text.match(/\S|$/)?.index || 0;
            const inStartingWhitespace = (
                selection.from >= startLine.from
                && selection.from <= startLine.from + firstNonWhitespaceOffset
            );

            if (completionStatus(editorState) === "active" && selectedCompletion(editorState) !== null) {
                return acceptCompletion(editorView);
            }

            if (inStartingWhitespace) {
                return false;
            }

            startCompletion(editorView);

            return true;
        }},
        {
            any(editorView: EditorView, event: KeyboardEvent) {
                if (event.key === "Escape") {
                    const state = editorView.state;
                    if (completionStatus(state) === "active") {
                        event.stopImmediatePropagation();
                        event.stopPropagation();
                        event.preventDefault();
                        closeCompletion(editorView);
                    }
                    return true;
                }
                return false;
            },
        }
    ];

    const enabledExtensions: Extension[] = [
        Prec.highest(keymap.of(overriddenKeymap)),
        EditorState.readOnly.of(false),
        EditorView.lineWrapping,
        [EditorView.theme({
            '.cm-scroller': {
                fontFamily: "'Ubuntu Mono', 'Courier New', Courier, monospace",
            }
        })],
        // highlightField,
        // EditorView.decorations.from(highlightField),
        // EditorView.theme({
        //     ".cm-error-highlight": {
        //         textDecoration: "wavy underline orange",
        //         position: "relative"
        //     }
        // })
    ];

    const language = LanguageRegistry.get("python");

    const autocompleteOptions = autocompletion({
        override: [(completion) => getCompletions(completion, session)],
        defaultKeymap: false,
        activateOnCompletion: language?.activateOnCompletion,
    });
    enabledExtensions.push(autocompleteOptions);

    if(language !== undefined) {
        const languageSupport: LanguageSupport = language.initializer({});
        enabledExtensions.push(
            languageSupport,
        )
    }

    const myLinter = linter(view => {
        return MOCK_ANNOTATIONS.map(annotation => {
            const annotationType = ANNOTATION_TYPES[annotation.error_type];
            const messageInfo = annotationType.message_table[annotation.error_id];
            
            return {
                from: annotation.start,
                to: annotation.end,
                severity: "error", // messageInfo.severity,
                message: messageInfo.title,
                // Rich HTML description with clickable link
                renderMessage() {
                    const el = document.createElement('div');
                    el.innerHTML = `
                        <div style="">
                            <h4 style="margin: 0px;">${messageInfo.title}</h4>
                            <p style="margin: 0px;">${messageInfo.description} <a href="${messageInfo.link}" target="_blank">Learn more</a>
                            </p>
                            <span style="display: none;"></span>
                        </div>
                    `;
                    return el;
                },
                // optional add actions that appear as buttons
                // actions: [{
                //     name: "Learn More",
                //     apply: () => window.open(messageInfo.link, '_blank')
                // }]
            }
        });
    });

    enabledExtensions.push(myLinter);
    enabledExtensions.push(lintGutter({
        // Customize hover delay (default is 300ms)
        hoverTime: 200,
        
        // Optional: Filter which diagnostics show markers
        markerFilter: (diagnostics) => {
            // Example: only show markers for errors and warnings
            return diagnostics.filter(d => 
                d.severity === "error" || d.severity === "warning"
            );
        },

        // Optional: Filter which diagnostics show in tooltips
        tooltipFilter: (diagnostics) => {
            // You could show different information in the tooltip
            // than what shows in the gutter
            return diagnostics;
        }
    }));

    return enabledExtensions;
});

</script>

<style lang="scss">

.sidemenu-container.left {
    min-width: 0px !important;
}

.chat-layout {
    display:flex;
    flex-direction: column;
    height: 100%;
    padding: 0 1rem;
    overflow-y: auto;
}

.jp-RenderedImage {
    img {
        width: 100%;
    }
}

div.footer-menu-bar {
    border-radius: 0px;
    padding-left: 0px;
}

.sidemenu-menu-selection.left {
    border-top: none;
    border-bottom: none;
    border-left: none;
}

.title {
    h4 {
        text-overflow: "clip";
        overflow: hidden;
        text-wrap: nowrap;
    }
}

div.status-container {
    min-width: 0px;
}

// .cm-error-highlight {
//     background-color: rgba(255, 0, 0, 0.1);
//     position: relative;
    
//     &:hover::after {
//         content: attr(title);
//         position: absolute;
//         left: 0;
//         bottom: -24px;
//         background: #AA8888; //#f44336;
//         color: white;
//         padding: 4px 8px;
//         border-radius: 4px;
//         font-size: 12px;
//         white-space: nowrap;
//         z-index: 1000;
//         box-shadow: 0 2px 4px rgba(0,0,0,0.2);
//     }
// }

.cm-diagnostic {
    white-space: normal;
}

// gutter markers
.cm-gutter-lint {
    width: 1.6em;
    
    // Style the marker container
    .cm-lint-marker {
        padding: 0.2em 0;
    }

    // Style markers by severity
    .cm-lint-marker-error {
        // color: blue;
        // content: "🔴"; // needs to be an svg
        // content: url("https://icons.terrastruct.com/essentials%2F073-add.svg");
        // content: url("https://icons.terrastruct.com/essentials%2F218-edit.svg");
    }
    
    .cm-lint-marker-warning {
        color: #ff9800;
    }
    
    .cm-lint-marker-info {
        color: #2196f3;
    }
}

// Make tooltips look better
.cm-tooltip.cm-tooltip-lint {
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 4px 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    
    ul {
        margin: 0;
        padding: 0;
    }
}

</style>
