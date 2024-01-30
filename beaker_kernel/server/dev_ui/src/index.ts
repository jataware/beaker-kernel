// @ts-nocheck
// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { PageConfig, URLExt } from '@jupyterlab/coreutils';
(window as any).__webpack_public_path__ = URLExt.join(
  PageConfig.getBaseUrl(),
  'example/'
);

import '@jupyterlab/application/style/index.css';
import '@jupyterlab/codemirror/style/index.css';
import '@jupyterlab/completer/style/index.css';
import '@jupyterlab/documentsearch/style/index.css';
import '@jupyterlab/notebook/style/index.css';
import '@jupyterlab/theme-light-extension/style/theme.css';
import '../index.css';

import { IYText } from '@jupyter/ydoc';
import {
  Toolbar as AppToolbar,
  CommandToolbarButton,
  SessionContextDialogs
} from '@jupyterlab/apputils';
import {
  CodeMirrorEditorFactory,
  CodeMirrorMimeTypeService,
  EditorExtensionRegistry,
  EditorLanguageRegistry,
  EditorThemeRegistry,
  ybinding
} from '@jupyterlab/codemirror';
import {
  Completer,
  CompleterModel,
  CompletionHandler,
  KernelCompleterProvider,
  ProviderReconciliator
} from '@jupyterlab/completer';
import { DocumentManager } from '@jupyterlab/docmanager';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { createMarkdownParser } from '@jupyterlab/markedparser-extension';
import { MathJaxTypesetter } from '@jupyterlab/mathjax-extension';
import {
  ExecutionIndicator,
  NotebookModelFactory,
  NotebookPanel,
  NotebookWidgetFactory,
  ToolbarItems
} from '@jupyterlab/notebook';
import { FileBrowserModel } from '@jupyterlab/filebrowser';
import {
  standardRendererFactories as initialFactories,
  RenderMimeRegistry
} from '@jupyterlab/rendermime';
import { ServiceManager } from '@jupyterlab/services';
import { Toolbar } from '@jupyterlab/ui-components';
import { CommandRegistry } from '@lumino/commands';
import { CommandPalette, SplitPanel, Widget, Panel } from '@lumino/widgets';

import { COMMAND_IDS, setupCommands } from './commands';



import { createMessage } from '@jupyterlab/services/lib/kernel/messages';


const baseUrl = PageConfig.getBaseUrl();

function main(): void {
  const manager = new ServiceManager();
  void manager.ready.then(() => {
    createApp(manager);
  });
}

async function createApp(manager: ServiceManager.IManager): void {
  // Initialize the command registry with the bindings.
  const commands = new CommandRegistry();
  const useCapture = true;

  // Setup the keydown listener for the document.
  document.addEventListener(
    'keydown',
    event => {
      commands.processKeydownEvent(event);
    },
    useCapture
  );

  // Fetch available contexts
  const url = URLExt.join(baseUrl, "/contexts");
  const response = await fetch(url);
  const contexts = await response.json();

  const languages = new EditorLanguageRegistry();

  const rendermime = new RenderMimeRegistry({
    initialFactories: initialFactories,
    latexTypesetter: new MathJaxTypesetter(),
    markdownParser: createMarkdownParser(languages)
  });

  const opener = {
    open: (widget: Widget) => {
      // Do nothing for sibling widgets for now.
    },
    get opened() {
      return {
        connect: () => {
          return false;
        },
        disconnect: () => {
          return false;
        }
      };
    }
  };

  const docRegistry = new DocumentRegistry();
  const docManager = new DocumentManager({
    registry: docRegistry,
    manager,
    opener
  });

  const mFactory = new NotebookModelFactory({});
  const editorExtensions = () => {
    const themes = new EditorThemeRegistry();
    EditorThemeRegistry.getDefaultThemes().forEach(theme => {
      themes.addTheme(theme);
    });
    const registry = new EditorExtensionRegistry();

    EditorExtensionRegistry.getDefaultExtensions({ themes }).forEach(
      extensionFactory => {
        registry.addExtension(extensionFactory);
      }
    );
    registry.addExtension({
      name: 'shared-model-binding',
      factory: options => {
        const sharedModel = options.model.sharedModel as IYText;
        return EditorExtensionRegistry.createImmutableExtension(
          ybinding({
            ytext: sharedModel.ysource,
            undoManager: sharedModel.undoManager ?? undefined
          })
        );
      }
    });
    return registry;
  };
  EditorLanguageRegistry.getDefaultLanguages()
    .filter(language =>
      ['ipython', 'julia', 'python'].includes(language.name.toLowerCase())
    )
    .forEach(language => {
      languages.addLanguage(language);
    });
  // Language for Markdown cells
  languages.addLanguage({
    name: 'ipythongfm',
    mime: 'text/x-ipythongfm',
    load: async () => {
      const m = await import('@codemirror/lang-markdown');
      return m.markdown({
        codeLanguages: (info: string) => languages.findBest(info) as any
      });
    }
  });
  const factoryService = new CodeMirrorEditorFactory({
    extensions: editorExtensions(),
    languages
  });
  const mimeTypeService = new CodeMirrorMimeTypeService(languages);
  const editorFactory = factoryService.newInlineEditor;
  const contentFactory = new NotebookPanel.ContentFactory({ editorFactory });

  const sessionContextDialogs = new SessionContextDialogs();

  const toolbarFactory = (panel: NotebookPanel) =>
    [
      COMMAND_IDS.save,
      COMMAND_IDS.insert,
      COMMAND_IDS.deleteCell,
      COMMAND_IDS.cut,
      COMMAND_IDS.copy,
      COMMAND_IDS.paste,
      COMMAND_IDS.runAndAdvance,
      COMMAND_IDS.interrupt,
      COMMAND_IDS.restart,
      COMMAND_IDS.restartAndRun
    ]
      .map<DocumentRegistry.IToolbarItem>(id => ({
        name: id,
        widget: new CommandToolbarButton({
          commands,
          id,
          args: { toolbar: true }
        })
      }))
      .concat([
        { name: 'cellType', widget: ToolbarItems.createCellTypeItem(panel) },
        { name: 'spacer', widget: Toolbar.createSpacerItem() },
        {
          name: 'kernelName',
          widget: AppToolbar.createKernelNameItem(
            panel.sessionContext,
            sessionContextDialogs
          )
        },
        {
          name: 'executionProgress',
          widget: ExecutionIndicator.createExecutionIndicatorItem(panel)
        }
      ]);


  const wFactory = new NotebookWidgetFactory({
    name: 'Notebook',
    modelName: 'notebook',
    fileTypes: ['notebook'],
    defaultFor: ['notebook'],
    preferKernel: true,
    canStartKernel: true,
    rendermime,
    contentFactory,
    mimeTypeService,
    toolbarFactory
  });

  docRegistry.addModelFactory(mFactory);
  docRegistry.addWidgetFactory(wFactory);

  const notebookPath = PageConfig.getOption('notebookPath');
  const fileBrowser = new FileBrowserModel({
      manager: docManager
  });
  // Use the filebrowser to check if the default file exists, and if not create it.
  let nbFileExists = false;
  await fileBrowser.refresh();
  const fileIter = fileBrowser.items();
  let fileItem = fileIter.next();
  while (fileItem && !fileItem.done) {
      if (fileItem.name == notebookPath) {
          nbFileExists = true;
      }
      fileItem = fileIter.next();
  }
  // Open default notebook if it exists, otherwise create a new notebook.
  const nbWidget = (nbFileExists
      ? docManager.open(notebookPath)
      : docManager.createNew(notebookPath, undefined, { name: "beaker_kernel" }));

  const notebook = nbWidget.content;
  const palette = new CommandPalette({ commands });
  palette.addClass('notebookCommandPalette');

  const editor =
    nbWidget.content.activeCell && nbWidget.content.activeCell.editor;
  const model = new CompleterModel();
  const completer = new Completer({ editor, model });
  const sessionContext = nbWidget.context.sessionContext;
  const timeout = 1000;
  const provider = new KernelCompleterProvider();
  const reconciliator = new ProviderReconciliator({
    context: { widget: nbWidget, editor, session: sessionContext.session },
    providers: [provider],
    timeout: timeout
  });
  const handler = new CompletionHandler({ completer, reconciliator });

  void sessionContext.ready.then(() => {
    const provider = new KernelCompleterProvider();
    const reconciliator = new ProviderReconciliator({
      context: { widget: nbWidget, editor, session: sessionContext.session },
      providers: [provider],
      timeout: timeout
    });

    handler.reconciliator = reconciliator;
  });

  const handleMessage = (context, msg) => {
    const msg_type = msg.header.msg_type;
    if (msg_type === "status") {
      return;
    }
    if (msg_type === "stream" && msg.parent_header?.msg_type == "llm_request") {
      notebook.model.cells.model.addCell({id: `${msg.id}-text`, cell_type: 'markdown', source: msg.content.text});
    }
    else if (msg_type === "llm_response") {
      const text = msg.content.text;
      const colored_text = `Response:<br/><span style="color: blue">${text}</span>`
      notebook.model.cells.model.addCell({id: `${msg.id}-text`, cell_type: 'markdown', source: colored_text});
    }
    else if (msg_type === "dataset") {
      dataPreview.textContent = formatDataPreview(msg.content);
    }
    else if (msg_type === "code_cell") {
      const code = msg.content.code;
      notebook.model.cells.model.addCell({id: `${msg.id}-code`, cell_type: 'code', source: code});
    }
    else if (msg_type === "llm_thought") {
      const text = msg.content.thought;
      const colored_text = `Thought: <span style="color: orange">${text}</span>`
      notebook.model.cells.model.addCell({id: `${msg.id}-text`, cell_type: 'markdown', source: colored_text});
    }
    else if (msg_type === "decapodes_preview") {
      const content = msg.content;
      dataPreview.innerHTML = `
        <div>${content["image/svg"]}</div>
        <div>${JSON.stringify(content["application/json"], null, 2)}</div>
      `;
    }
    else if (msg.msg_type === "debug_event") {
      console.log("beaker-debug", `${msg.content.event}`, msg.content.body);
    }
    else {
      console.log("Unhandled message:", msg);
    }
  }

  void sessionContext.ready.then(() => {
    const session = sessionContext.session;
    // const kernel = session?.kernel;
    session?.iopubMessage.connect(handleMessage);
  });

  // Set the handler's editor.
  handler.editor = editor;

  // Listen for active cell changes.
  notebook.activeCellChanged.connect((sender, cell) => {
    handler.editor = cell && cell.editor;
  });

  // Hide the widget when it first loads.
  completer.hide();

  const formatDataPreview = (preview) => {
    const output = [];
    for (const dataset of Object.keys(preview)){
      output.push(`Dataset "${dataset}":\n`)
      for (const line of preview[dataset].csv) {
        output.push(line.join(","));
      }
      output.push("\n");
    }
    return output.join("\n");
  };

  const setKernelContext = (context_info) => {
    const session = sessionContext.session;
    const kernel = session?.kernel;
    const messageBody = {
      session: session?.name || '',
      channel: 'shell',
      content: context_info,
      msgType: 'context_setup_request',
      msgId: `${kernel.id}-setcontext`
    };
    const message: JupyterMessage = createMessage(messageBody);
    kernel?.sendShellMessage(message);
  };


  const sendLLMQuery = (query: string) => {
    const session = sessionContext.session;
    const kernel = session?.kernel;
    if (kernel) {
      const message: JupyterMessage = createMessage({
        session: session?.name || '',
        channel: 'shell',
        content: { request: query },
        msgType: 'llm_request',
        msgId: `${kernel.id}-query`
      });
      const colored_text = `LLM Query: <span style="color: green; font-weight: bold">${query}</span>`
      notebook.model.cells.model.addCell({id: `${message.header.msg_id}-text-${Date.now()}`, cell_type: 'markdown', source: colored_text});
      kernel.sendShellMessage(message);
    }

  };

  const sendCustomMessage = (channel: string, msgType: string, content: Object) => {
    const session = sessionContext.session;
    const kernel = session?.kernel;
    if (kernel) {
      const timestamp = new Date().toISOString();
      const message: JupyterMessage = createMessage({
        session: session?.name || '',
        channel: channel,
        content: content,
        msgType: msgType,
        msgId: `${kernel.id}-${msgType}-timestamp`
      });
      console.log("Sending custom message", message);
      if (channel === "shell") {
        kernel.sendShellMessage(message);
      }
      // else if (channel)
      else {
        // TODO: Determine if we actually have to do something different here
        kernel.sendShellMessage(message);
      }
    }

  };

  const llmWidget = new Widget();
  const llmContainer = document.createElement('div');
  const llmNode = document.createElement('input');
  const llmButton = document.createElement('button');
  const llmHeader = document.createElement('h1');
  llmHeader.textContent = "LLM interaction";
  llmContainer.appendChild(llmHeader);
  llmContainer.appendChild(llmNode);
  llmContainer.appendChild(llmButton);
  llmNode.id = "llmQueryInput";
  llmNode.placeholder = 'Enter LLM query:';
  llmNode.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      sendLLMQuery(llmNode.value);
    }
  }, false);
  llmButton.addEventListener("click", (e) => {
    sendLLMQuery(llmNode.value);
  }, false);
  llmButton.textContent = "Submit";
  llmWidget.node.appendChild(llmContainer);

  const setContext = () => {
    languageSelect.innerHTML = '';
    const contextInfo = contexts[contextSelect.value];
    contextInfo.languages.forEach((lang) => {
      console.log(lang);
      const option = document.createElement('option');
      option.setAttribute("label", lang.slug);
      option.setAttribute("value", lang.subkernel);
      languageSelect.appendChild(option);
    });
    contextPayloadInput.value = contextInfo.defaultPayload;
  };

  const contextWidget = new Widget();
  const contextNode = document.createElement('div');
  const contextSelect = document.createElement('select');
  const languageSelect = document.createElement('select');
  const contextPayloadInput = document.createElement('textarea');
  const contextDebug = document.createElement('input');
  const contextDebugLabel = document.createElement('label');
  const contextVerbose = document.createElement('input');
  const contextVerboseLabel = document.createElement('label');
  const contextButton = document.createElement('button');
  const contextHeader = document.createElement('h2');
  const contextSelectionHolder = document.createElement('span');
  const contextDivTop = document.createElement('div');
  const contextDivBottom = document.createElement('div');

  contextHeader.textContent = "Context setup";
  contextNode.id = 'context-node';
  for (const context of Object.keys(contexts)){
    const option = document.createElement('option');
    option.setAttribute("value", context);
    option.setAttribute("label", context);
    contextSelect.appendChild(option);
  }
  contextSelect.onchange = setContext;

  contextDebug.type = "checkbox";
  contextDebug.id = "context-debug-input";
  contextDebug.name = "context-debug-input";
  contextDebugLabel.innerText = "Debug";
  contextDebugLabel.setAttribute("for", "context-debug-input");
  contextVerbose.type = "checkbox";
  contextVerbose.id = "context-verbose-input";
  contextVerbose.name = "context-verbose-input";
  contextVerboseLabel.innerText = "Verbose";
  contextVerboseLabel.setAttribute("for", "context-verbose-input");

  contextPayloadInput.className = 'json-input';
  contextPayloadInput.value = '';
  contextButton.textContent = 'Submit';
  contextButton.addEventListener("click", (e) => {
    setKernelContext({
      context: contextSelect.value,
      language: languageSelect.value,
      context_info: JSON.parse(contextPayloadInput.value),
      debug: contextDebug.checked,
      verbose: contextVerbose.checked,
    })
  }, false);
  contextSelectionHolder.style.display = 'inline-block';
  contextNode.appendChild(contextHeader);
  contextDivTop.appendChild(contextDebugLabel);
  contextDivTop.appendChild(contextDebug);
  contextDivTop.appendChild(contextVerboseLabel);
  contextDivTop.appendChild(contextVerbose);
  contextDivBottom.appendChild(contextSelect);
  contextDivBottom.appendChild(languageSelect);
  contextSelectionHolder.appendChild(contextDivTop);
  contextSelectionHolder.appendChild(contextDivBottom);
  contextNode.appendChild(contextSelectionHolder);
  contextNode.appendChild(contextPayloadInput);
  contextNode.appendChild(contextButton);
  contextWidget.node.appendChild(contextNode);

  const messageWidget = new Widget();
  const messageNode = document.createElement('div');
  const messageHeader = document.createElement('h2');
  const messageTypeInput = document.createElement('input');
  const messageChannelSelect = document.createElement('select');
  const messagePayloadInput = document.createElement('textarea');
  const messageButton = document.createElement('button');

  messageNode.appendChild(messageHeader);
  messageNode.appendChild(messageTypeInput);
  messageNode.appendChild(messageChannelSelect);
  messageNode.appendChild(messagePayloadInput);
  messageNode.appendChild(messageButton);
  messageWidget.node.appendChild(messageNode);

  messageButton.textContent = "Submit";
  messageButton.onclick = (evt) => {
    console.log("click event:", evt);
    let channel = messageChannelSelect.value;
    let msgType = messageTypeInput.value;
    let contentString = messagePayloadInput.value;
    let content;
    try {
      content = JSON.parse(contentString);
    }
    catch(err) {
      alert("Error: message content must be able to parse to JSON");
      return;
    }
    sendCustomMessage(channel, msgType, content);
  };

  messageHeader.textContent = "Custom Message:";
  messageTypeInput.placeholder = "Message type name";

  messageChannelSelect.innerHTML = `
    <option value="shell">shell</option>
    <option value="iopub">iopub</option>
    <option value="stdin">stdin</option>
    <option value="control">control</option>
    <option value="hb">hb</option>
  `;
  messageChannelSelect.onchange = (evt) => {console.log(evt);}

  const dataPreviewWidget = new Widget();
  const dataPreviewHeader = document.createElement('h2');
  const dataPreview = document.createElement('div');
  dataPreview.id = 'preview';
  dataPreviewHeader.textContent = "Preview:";
  dataPreviewWidget.node.appendChild(dataPreviewHeader);
  dataPreviewWidget.node.appendChild(dataPreview);

  const leftPanel = new Panel();
  leftPanel.id = 'left';
  leftPanel.orientation = 'vertical';
  leftPanel.spacing = 0;
  leftPanel.node.style.overflowY = "auto";
  leftPanel.addWidget(llmWidget);
  leftPanel.addWidget(contextWidget);
  leftPanel.addWidget(messageWidget);
  leftPanel.addWidget(dataPreviewWidget);

  const mainPanel = new SplitPanel();
  mainPanel.id = 'main';
  mainPanel.orientation = 'horizontal';
  mainPanel.spacing = 0;
  SplitPanel.setStretch(leftPanel, 1);
  SplitPanel.setStretch(nbWidget, 2);
  mainPanel.addWidget(leftPanel);
  mainPanel.addWidget(nbWidget);

  // Attach the panel to the DOM.
  Widget.attach(mainPanel, document.body);
  Widget.attach(completer, document.body);

  // Handle resize events.
  window.addEventListener('resize', () => {
    mainPanel.update();
  });

  setupCommands(commands, palette, nbWidget, handler, sessionContextDialogs);
  setContext();

  console.debug('Example started!');
}

window.addEventListener('load', main);
