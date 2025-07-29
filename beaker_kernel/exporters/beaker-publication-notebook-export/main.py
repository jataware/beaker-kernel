from nbformat import NotebookNode
from traitlets.config import default
from nbconvert.exporters.notebook import NotebookExporter
from nbconvert.preprocessors import Preprocessor
from archytas.models.base import BaseArchytasModel

from typing import TypedDict

class PublicationOptions(TypedDict):
    collapseCodeCells: bool
    collapseOutputs: bool
    cleanAgentErrors: bool

class PublicationPreprocessor(Preprocessor):
    def __init__(self, **kwargs):
        self.model: BaseArchytasModel | None = None
        self.options: dict | None = None
        super().__init__(**kwargs)
    def preprocess(self, nb: NotebookNode, resources: dict):
        for index, cell in enumerate(nb.cells):
            nb.cells[index], resources = self.preprocess_cell(cell, resources, index)
        nb.cells = [cell for cell in nb.cells if not cell.metadata.get("omitted", False)]
        return nb, resources
    def preprocess_cell(self, cell: NotebookNode, resources: dict, index: int):
        if self.model is None:
            raise ValueError("Failed to retrieve model")
        if cell.cell_type == "markdown":
            if cell.metadata.get("finalResponse"):
                message = self.model.invoke([f"""
                    Here is a message from an AI agent, written in first person.
                    Strip all markdown formatting and HTML tags before adding your own for clarity.
                    Please rewrite this to be a declarative third person statement about what was done in past tense with no self talk.
                    Rather than say "The agent performed this action", say "This action was performed" in passive voice.
                    Do not say I. Preferably, do not talk about an agent at all.

                    Start with a heading in markdown (h1 or h2) in this block.

                    {cell.source}"""])
            elif cell.metadata.get("parentQueryCell"):
                message = self.model.invoke([f"""
                    Here is a user query to run code on the user's behalf.
                    Please preserve the formatting as a markdown header.
                    Please rewrite this to be a present participle statement about what is going to be done.
                    Examples:
                    IN: "can you plot a sine wave?"
                    OUT: "# Creating a sine wave"
                    IN: "Please fetch data from this data repository"
                    OUT: "# Fetching data from data repository"
                    IN: "Can you create a table of random data
                    ```python
                    # numpy code to create a table
                    ```"
                    OUT: "# Creating a table of random data with Numpy"
                    as if filling out a table of contents.

                    Do not include anything but the header here.
                    Instead of code blocks, leave only the header.
                    Code will be added later, so do not create any annotated code blocks or summaries.

                    {cell.source}"""])
            elif cell.metadata.get("beakerQueryCellChild"):
                message = self.model.invoke([f"""
                    Here is a message from an AI agent, written in first person.
                    Strip all markdown formatting and HTML tags before adding your own for clarity.
                    Please rewrite this to be a declarative third person statement about what was done in past tense with no self talk.
                    Rather than say "The agent performed this action", say "This action was performed" in passive voice.
                    Do not say I. Preferably, do not talk about an agent at all.

                    This is an intermediate step, so please keep it terse.
                    Avoid starting statements with interjections like "Perfect!" or "Excellent!" and remove these if present.

                    {cell.source}"""])
            cell.source = f'{message.content}'
        elif cell.cell_type == "code":
            if cell.metadata.get("beakerQueryCellChild") and self.options:
                if self.options.get("collapseCodeCells"):
                    cell.metadata["collapsed"] = True
                    cell.metadata["jupyter"] = cell.metadata.get("jupyter", {}) | {"source_hidden": True}
                if self.options.get("collapseOutputs"):
                    cell.metadata["jupyter"] = cell.metadata.get("jupyter", {}) | {"outputs_hidden": True}
                if self.options.get("cleanAgentErrors"):
                    if "error" in [output.output_type for output in cell.outputs]:
                        cell.metadata["omitted"] = True
        return cell, resources


class PublicationExporter(NotebookExporter):
    """
    Exports a notebook with LLM passes to focus and sharpen the information
    to make publication ready.
    """
    export_from_notebook = "Publication Notebook"
    output_mimetype = "application/json"

    def __init__(self, **kwargs):
        self.preprocessors = [PublicationPreprocessor]
        self.model: BaseArchytasModel | None = None
        self.options: dict | None = None
        super().__init__(**kwargs)

    @default("file_extension")
    def _file_extension_default(self):
        return ".ipynb"

    def from_notebook_node(self, nb: NotebookNode, resources=None, **kwargs):
        if self.model is None:
            raise ValueError("Failed to get model from Beaker Kernel")
        publication_preprocessor = next(
            preprocessor for preprocessor in self._preprocessors
            if isinstance(preprocessor, PublicationPreprocessor)
        )
        publication_preprocessor.model = self.model
        publication_preprocessor.options = self.options
        output, resources = super().from_notebook_node(nb, resources, **kwargs)
        return output, resources
