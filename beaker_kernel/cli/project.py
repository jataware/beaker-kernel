import click
import copy
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


# HATCH_CONFIG_FILE_CONTENTS = """\
# [template.plugins.default]
# [template.plugins.beaker-new-project]
# """
# # [template.plugins.beaker-new-context]
HATCH_NEW_PROJECT_CONFIG_FILE_DEFAULTS = {
    'template': {
        'plugins': {
            'default': {},
            'beaker-new-project': {},
        },
    }
}

@click.group(name="project")
def project():
    """
    Beaker project management
    """
    pass

@project.command(name="new")
@click.argument(
    "name",
    required=False,
)
@click.option(
    "--no-interaction", "-n", "no_interact",
    type=bool,
    is_flag=True,
    default=False,
    help="Do not prompt for any information. Will fail if `name` is not provided."
)
@click.option(
    "--dependency", "-d", "dependencies",
    multiple=True,
    help="A dependency to include in the pyproject. Example: 'pandas>=3.2.0'"
)
@click.option(
    "--no-context", "-c", "no_context",
    type=bool,
    is_flag=True,
    default=False,
    help="Do not include a sample context."
)
@click.pass_context
def new_project(ctx: click.Context, name, no_interact, dependencies, no_context):
    """
    Creates a new Beaker Python project.

    This project can add new context(s) and/or subkernels to Beaker as an additional Python library.

    NAME is used for both the generated directory and project name in pyproject.toml. The convention is to split words
    with dashes (-) instead of underscores or using CamelCase.
    If NAME is not provided you will be prompted, unless --no-interaction.
    """
    dependencies = list(dependencies)

    normalized_name = None
    while not name or not normalized_name:
        if name:
            normalized_name = normalize_project_name(re.sub(r'\s', '.', name))
            if name != normalized_name:
                if not no_interact:
                    click.echo(
                        "PEP-503 (https://peps.python.org/pep-0503/#normalized-names) suggests normalization of "
                        "package names.")
                    if click.confirm(f"Use normalized name '{normalized_name}' instead?", default=True):
                        name = normalized_name
                        continue
                else:
                    click.echo(
                        f"Notice: package name '{name}' does not confirm to the normalization defined in PEP-503 "
                        "(https://peps.python.org/pep-0503/#normalized-names).\n"
                        "However proceeding with provided name since --no-interaction flag has been set."
                    )
            if re.search(r'\s', name):
                if not no_interact:
                    click.echo(f"Name cannot contain whitespace ('{name}' entered).")
                    name = None
                    normalized_name = None
                    continue
                else:
                    raise click.ClickException(f"Name cannot contain whitespace ('{name}' entered).")
        else:
            if not no_interact:
                while not name:
                    name = click.prompt("Project name")
            else:
                raise click.ClickException("A name is a required argument when the --no-interaction flag is set.")

    # Additional dependencies
    if not no_interact:
        if click.confirm("Would you like to provide additional dependencies now?", default=False):
            click.echo("Leave blank to finish.")
            while dependency := click.prompt("Dependency definition", default="", show_default=False):
                dependencies.append(dependency)

    if not no_context:
        if no_interact:
            class_base_name_default = ''.join(word.capitalize() for word in normalized_name.split('-'))
            context_config = {
                "context_name": normalized_name,
                "class_base_name": class_base_name_default,
            }
        else:
            if click.confirm("Would you like to include an example context?", default=True):
                from . import context
                context_config = context.prompt_for_missing_new_context_options(
                    {},
                    defaults={
                        "context_name": name,
                    }
                )
            else:
                context_config = {}
    else:
        context_config = {}

    # Define hatch config
    hatch_config = copy.deepcopy(HATCH_NEW_PROJECT_CONFIG_FILE_DEFAULTS)
    project_config = hatch_config['template']['plugins']['beaker-new-project']
    project_config['package-name'] = name
    project_config['dependencies'] = dependencies
    if context_config:
        hatch_context_config = {key.replace("_", "-"): value for key, value in context_config.items()}
        hatch_config['template']['plugins']['beaker-new-context'] = hatch_context_config

    # Execute hatch new to create the project
    args = [sys.executable, '-m', 'hatch', 'new', name]
    environ = os.environ.copy()
    with tempfile.NamedTemporaryFile('w') as tempconfig:
        tempconfig.write(toml.dumps(hatch_config))
        tempconfig.flush()
        environ.update({
            "HATCH_CONFIG": tempconfig.name,
        })
        result = subprocess.call(args, env=environ)
        if result > 0:
            raise click.ClickException("There was an error setting up your new Beaker project. Please check the output above.")


# @project.command()
# @click.argument("project_name", required=False, default=None)
# def info(project_name):
#     """
#     Information about a project. Looks for a project in current location if no project name is provided.
#     """
#     pass
