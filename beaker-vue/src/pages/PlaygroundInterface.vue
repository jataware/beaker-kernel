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

import { defineProps, inject, ref, computed, ComponentInstance, Component, StyleHTMLAttributes, ComputedRef, shallowRef, toRaw } from 'vue';

import { IBeakerTheme } from '../plugins/theme';

import { Codemirror } from "vue-codemirror";
import { EditorView, keymap } from "@codemirror/view";
import { EditorState, Extension, Prec, StateField, StateEffect } from "@codemirror/state";
import { LanguageSupport } from "@codemirror/language";
import { autocompletion, completionKeymap, completionStatus, selectedCompletion, acceptCompletion, closeCompletion, startCompletion } from "@codemirror/autocomplete";
import { BeakerLanguage, LanguageRegistry, getCompletions } from "../util/autocomplete";
import { BeakerSession } from 'beaker-kernel/src';
import { linter, Diagnostic, lintGutter, forceLinting, setDiagnostics } from "@codemirror/lint";
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
                "link": "https://lmgtfy.com/",
                "severity": "warning",
            },
            "assumption_in_value": {
                "title": "Assumption in value",
                "description": "The following assumption was made with regards to the value of this variable:\n",
                "link": "https://lmgtfy.com/",
                "severity": "warning",
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

// codemirror severity: "error" | "hint" | "info" | "warning"
const SEVERITY_MAPPINGS = {
    "major": "error",
    "warning": "warning",
    "info": "info",
    "hint": "hint"
};

const sampleCode = ref(sampleCodeText);
const model = ref<string>(sampleCode.value);

const codeMirrorView = shallowRef<EditorView>();
const codeMirrorState = shallowRef();
const currentAnnotations = ref<typeof MOCK_ANNOTATIONS>([]);

// Create diagnostic objects from annotations
const createDiagnosticFromAnnotation = (annotation: typeof MOCK_ANNOTATIONS[0]): Diagnostic => {
  const annotationType = ANNOTATION_TYPES[annotation.error_type];
  const messageInfo = annotationType.message_table[annotation.error_id];

  return {
    from: annotation.start,
    to: annotation.end,
    severity: SEVERITY_MAPPINGS[messageInfo.severity],
    message: messageInfo.title,
    markClass: "cm-diagnostic-beaker",
    renderMessage() {
      const el = document.createElement('div');
      el.innerHTML = `<h4 style="margin: 0.2rem 0">${messageInfo.title}</h4><p>${messageInfo.description}</p><a href="${messageInfo.link}" target="_blank">Learn more</a>`;
      return el;
    },
  };
};

// Mock service that would fetch annotations from a backend
const fetchAnnotations = () => {
  // Simulate API delay
  setTimeout(() => {
    // Simulate first batch of annotations
    console.log("Adding first annotation");
    currentAnnotations.value = [MOCK_ANNOTATIONS[0]];
    updateDiagnostics();
    
    // Simulate second batch coming in later
    setTimeout(() => {
      console.log("Adding second annotation");
      currentAnnotations.value = [...MOCK_ANNOTATIONS];
      updateDiagnostics();
    }, 4000);
  }, 2000);
};

// Function to update diagnostics in the editor
const updateDiagnostics = () => {
  if (codeMirrorView.value) {
    // console.log("Updating diagnostics with:", toRaw(currentAnnotations.value));
    
    // Convert annotations to diagnostics
    const diagnostics = currentAnnotations.value.map(annotation => 
      createDiagnosticFromAnnotation(annotation)
    );
    
    // Use the setDiagnostics function to directly set diagnostics
    codeMirrorView.value.dispatch(
      setDiagnostics(codeMirrorView.value.state, diagnostics)
    );
  }
};

const handleReady = ({view, state}) => {
  codeMirrorView.value = view;
  codeMirrorState.value = state;
  
  // Start the mock service to fetch annotations
  fetchAnnotations();
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

    // Create a custom linter that responds to our state effect
    const myLinter = linter((view) => {
        console.log("Linter running with annotations:", currentAnnotations.value);
        return currentAnnotations.value.map(annotation => createDiagnosticFromAnnotation(annotation));
    }, {
        // Set delay to 0 to run immediately when triggered
        delay: 0
    });

    enabledExtensions.push(myLinter);
    enabledExtensions.push(lintGutter({
        hoverTime: 200,
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

// increasing wiggle lines size slightly (easier to see)
.cm-lintRange {
    background-size: 0.45rem;
}

// for gutter markers
.cm-gutter-lint {
    width: 1.6em;
    
    // marker container
    .cm-lint-marker {
        padding: 0.2em 0;
    }

    .cm-lint-marker-error {

        content: ""; /* clear the default content which requires an svg */
        position: relative;
    
        &::before {
            // content: "\e90b"; /* unicode for pi-times icon */
            // content: "";   // pasting pi-times-circle from website, but below is better
            // content: "\e90c"; /* unicode for pi-times-circle icon */
            content: ""; /* character for pi-exclamation-circle icon */
            font-family: 'PrimeIcons';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: rgb(236, 77, 77);
            font-size: 0.9rem;
        }
    }
    
    .cm-lint-marker-warning {
        content: ""; /* clear the default content which requires an svg */
        position: relative;
    
        &::before {
            font-family: 'PrimeIcons';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 0.9rem;
            color: #ff9800;
            content: ""; // exclamation triangle char
        }

    }
    
    .cm-lint-marker-info {

        content: ""; /* clear the default content which requires an svg */
        position: relative;
    
        &::before {
            font-family: 'PrimeIcons';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 0.9rem;
            color: #2196f3;
            content: ""; // exclamation triangle char
        }
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
