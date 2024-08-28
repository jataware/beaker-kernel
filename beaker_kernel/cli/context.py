import click
import tempfile
import hatch
import os
import re
import string
import subprocess
import sys
import toml
import hatch.cli
import hatch.cli.application
import hatch.project
import hatch.project.utils
from hatchling.metadata.utils import normalize_project_name


@click.group(name="context")
def context():
    """
    Commands for creating a new context.
    """
    pass


@context.command(name="new")
@click.argument(
    "name",
    required=False,
)
@click.option(
    "--class-base-name", "-c", "class_base_name",
    type=str,
    help="Base root name for generating classes such as the subclasses of BeakerContext and BeakerAgent.",
)
def new_context(name, class_base_name):
    """
    Creates a new context in the current project.
    """
    options = {
        "context_name": name,
        "class_base_name": class_base_name,
    }

    pass


@context.command(name="list")
def list_contexts():
    """
    List installed contexts.
    """
    pass


def prompt_for_missing_new_context_options(options: dict[str, any], defaults: dict[str, any] | None = None) -> dict[str, any]:
    if not defaults:
        defaults = {}

    if "context_name" not in options:
        options["context_name"] = click.prompt("Name for the context", default=defaults.get("context_name", None))
    if "class_base_name" not in options:
        class_base_name_default_base: str = defaults.get("class_base_name", options["context_name"])
        class_base_name_default = ''.join(word.capitalize() for word in class_base_name_default_base.split('-'))
        options["class_base_name"] = click.prompt("Base Name for generated classes", default=class_base_name_default)
    if "context_subdirectory" not in options:
        options["context_subdirectory"] = click.prompt("Sub-directory to write context files (default: no subdirectory)", default="") or None

    return options
