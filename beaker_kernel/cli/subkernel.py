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


@click.group(name="subkernel")
def subkernel():
    """
    Commands for creating a new subkernel.
    """
    pass


@subkernel.command(name="new")
def new_subkernel():
    """
    Create a new subkernel.
    """
    pass


@subkernel.command(name="list")
def list_subkernels():
    """
    List installed subkernels.
    """
    pass
