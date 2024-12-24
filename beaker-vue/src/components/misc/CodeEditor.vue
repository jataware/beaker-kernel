<template>
    <Codemirror
        v-model="model"
        :extensions="extensions"
        :disabled="props.disabled"
        :autofocus="props.autofocus"
        @ready="handleReady"
        @update:modelValue="modelUpdate"
    />
</template>

<script setup lang="ts">
import { defineProps, defineModel, ref, defineEmits, defineExpose, shallowRef, computed, withDefaults, inject } from "vue";
import { Codemirror } from "vue-codemirror";
import { EditorView, keymap } from "@codemirror/view";
import { EditorState, Extension, Prec } from "@codemirror/state";
import { LanguageSupport } from "@codemirror/language";
import { autocompletion, CompletionSource, completionKeymap } from "@codemirror/autocomplete";
import { python } from "@codemirror/lang-python";
import { r } from 'codemirror-lang-r';
import { markdown } from "@codemirror/lang-markdown";
import { oneDark } from "@codemirror/theme-one-dark";
import { json } from "@codemirror/lang-json";
import { javascript } from "@codemirror/lang-javascript";
import { julia } from "@plutojl/lang-julia";
import { Completion, CompletionContext, CompletionResult, completionStatus, selectedCompletion, acceptCompletion, startCompletion, closeCompletion } from "@codemirror/autocomplete";
import * as messages from '@jupyterlab/services/lib/kernel/messages';
import { IBeakerTheme } from '../../plugins/theme';
import { BeakerSession, IBeakerFuture } from 'beaker-kernel/src';

declare type DisplayMode = "light" | "dark";
declare type BeakerLanguage = "python" | "julia" | "markdown" | "json" | "javascript" | string;

const session: BeakerSession = inject('session');

const languageMap: {[key: string]: (options: any) => LanguageSupport} = {
    python,
    python3: python,
    python2: python,
    julia,
    markdown,
    json,
    javascript,
    rlang: r,
    r,
    ir: r,
}

declare interface Props {
    displayMode: DisplayMode,
    language?: BeakerLanguage,
    languageOptions?: any,
    modelValue: string,

    autofocus?: boolean,
    disabled?: boolean,
}

declare interface JupyterTypedCompletion {
    start: number;
    end: number;
    text: string;
    type: "keyword" | "path" | "magic" | "variable" | string;
    signature?: string;
}

const props = withDefaults(defineProps<Props>(), {
    displayMode: "light",
    autofocus: false,
    disabled: false,
});

const model = ref<string>(props.modelValue);

const emit = defineEmits([
        'submit',
        "update:modelValue",
]);
const { theme, toggleDarkMode } = inject<IBeakerTheme>('theme');

const codeMirrorView = shallowRef<EditorView>();
const codeMirrorState = shallowRef();

const handleReady = ({view, state}) => {
    // See vue codemirror api/npm docs: https://codemirror.net/docs/ref/
    codeMirrorView.value = view;
    codeMirrorState.value = state;
};

const modelUpdate = (newValue: string): void => {
    emit("update:modelValue", newValue);
}

const displayMode = computed<DisplayMode>(() => {
    if (theme.mode === 'default') {
        return 'light';
    }
    else {
        return theme.mode;
    }
});

const extensions = computed(() => {
    const filteredCompletionKeymap = completionKeymap.filter(item => !['Tab', 'Escape'].includes(item.key));
    const overriddenKeymap = [
        ...filteredCompletionKeymap,
        {key: "Tab", run: (editorView) => {
            const state = editorView.state;
            const selection = state.selection.main;
            const lineStartRegex = new RegExp("^\\s*$", "m");
            const endOfWordRegex = new RegExp("^\\w(\\b|$)","m");
            if (completionStatus(state) === "active" && selectedCompletion(state) !== null) {
                return acceptCompletion(editorView);
            }
            if (selection.empty && endOfWordRegex.test(state.sliceDoc(selection.to - 1, selection.to + 1))) {
                return true;

            }
            // Don't indent cursor isn't a in the middle of a line
            if (selection.empty && !lineStartRegex.test(state.sliceDoc(0, selection.to))) {
                return true;
            }


            return false;
        }},
        // Prevent escape key from exiting cell editing if autocomplete is cancelled by pressing exec.
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
        // Keymapping
        Prec.highest(keymap.of(overriddenKeymap)),
        EditorView.lineWrapping,
        [EditorView.theme({
            '.cm-scroller': {
                fontFamily: "'Ubuntu Mono', 'Courier New', Courier, monospace",
            }
        })],
    ];
    if (displayMode.value === "dark") {
        enabledExtensions.push(oneDark);
    }
    const autocompleteOptions = autocompletion({
        override: [getCompletions],
        defaultKeymap: false,
        // activateOnCompletion: (completion) => {
        //     console.log("DEADBEEF!!!!", completion, this);
        //     // console.log("activateOnCompletion", completion);
        //     return false
        // },
    });
    enabledExtensions.push(autocompleteOptions);
    if(props.language !== undefined) {
        let language: LanguageSupport = languageMap[props.language](props.languageOptions);
        enabledExtensions.push(
            language,
        )
    }
    return enabledExtensions;
});

const getCompletions = async (completionContext: CompletionContext): Promise<CompletionResult | null>  => {
    const code = completionContext.state.doc.toString();
    const cursor_pos = completionContext.pos;
    let matchbefore = completionContext.matchBefore(/[#_([{\w]{1,}/);

    if (!matchbefore && !completionContext.explicit) {
        return null;
    }

    // Get autocompletions from subkernel
    const complete_request: IBeakerFuture<messages.ICompleteRequestMsg, messages.ICompleteReplyMsg> = session.sendBeakerMessage(
        "complete_request",
        {
            "code": code,
            "cursor_pos": cursor_pos,
        }
    )

    // While the kernel is processing the request, get the language autocompletes to filter against.
    const languageAutocompletes = completionContext.state.languageDataAt("autocomplete", 0);
    let promises: Promise<CompletionResult>[] = [];
    if (Array.isArray(languageAutocompletes)) {
        languageAutocompletes.forEach((autocomplete) => {
            const result = autocomplete(completionContext);
            promises.push(Promise.resolve(result));
        })
    }
    else {
        throw Error("languageAutoCompletes is not a list?!?!")
    }
    let results: CompletionResult[] = await Promise.all(promises);

    const languageOptions: Completion[] = results.flatMap((result) => result.options);
    const complete_reply = await complete_request.done;
    let from: number, to: number;

    if (results.length > 1) {
        from = results.map(result => result.from).reduce((prevResult, result,) => {
            return (prevResult === result ? prevResult : undefined);
        });
        to = results.map(result => result.to).reduce((prevResult, result,) => {
            return (prevResult === result ? prevResult : undefined);
        });
    }
    else if (results.length === 1) {
        from = results[0].from;
        to = results[0].to;
    }
    else {
        from = undefined;
        to = undefined;
    }

    let kernelResults: Completion[] = [];
    let kernelOptions: Set<string> = new Set([]);
    if (complete_reply.content.status === "ok") {
        if (complete_reply.content.cursor_start === from || from === undefined) {
            from = complete_reply.content.cursor_start;
        }
        else {
            console.error("Cannot complete as `from` value differs");
        }
        if (complete_reply.content.cursor_end === to || to === undefined) {
            to = complete_reply.content.cursor_end;
        }
        else {
            console.error("Cannot complete as `to` value differs");
        }

        if ((complete_reply.content.metadata?._jupyter_types_experimental as [])?.length > 0) {
            let typed_options: JupyterTypedCompletion[] = complete_reply.content.metadata._jupyter_types_experimental as unknown as JupyterTypedCompletion[];
            kernelResults = typed_options.map((option) => {
                const boost = (option.type == "param" ? 50 : 5);
                return {
                    label: option.text,
                    type: option.type,
                    boost: boost,
                    detail: (option.signature !== "" ? option.signature : undefined),
                }
            });
            kernelOptions = new Set(typed_options.map(option => option.text))
        }
        else if (complete_reply.content.matches?.length > 0) {
            kernelResults = complete_reply.content.matches.map((option) => {
                    const boost = (option.endsWith("=") ? 50 : 5);

                    return {
                        label: option,
                        boost: boost,
                    }
                });
            kernelOptions = new Set(complete_reply.content.matches)
        }
    }
    const options = [...kernelResults, ...languageOptions.filter(option => !kernelOptions.has(option.label))];
    return {
        from,
        to,
        filter: false,
        options,
    };
};

const focus = () => {
    codeMirrorView.value?.focus();
}

const blur = () => {
    codeMirrorView.value?.contentDOM?.blur();
}

defineExpose({
    focus,
    blur,
    view: codeMirrorView,
    update: modelUpdate,
    model: model
})

</script>

<style lang="scss">
    .cm-completionIcon-instance {
        &::after {
            content: '𝑥';
        }
    }

</style>
