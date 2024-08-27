import click
import copy
import inspect
import os
import subprocess
import sys
import tempfile
import toml
from hatch.project.core import Project
from hatchling.builders.plugin.interface import BuilderInterface
from hatchling.metadata.utils import normalize_project_name

# Manual "import" of a static method as it acts like a normal function
normalize_file_name_component = BuilderInterface.normalize_file_name_component

from .helpers import find_pyproject_file


HATCH_NEW_CONTEXT_CONFIG_FILE_DEFAULTS = {
    'template': {
        'plugins': {
        },
    }
}


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
    pyproject_path = find_pyproject_file()
    if not pyproject_path:
        raise click.ClickException("You do not seem to be running within a valid project.")
    project = Project(pyproject_path)

    for project_name in (
        normalize_file_name_component(project.metadata.core.raw_name),
        normalize_file_name_component(project.metadata.core.name),
    ):
        project_source_path = project.root / project_name

        if (project_source_path / '__init__.py').is_file():
            break

        project_source_path = project.root / 'src' / project_name
        if (project_source_path / '__init__.py').is_file():
            break

    else:
        raise click.ClickException("You do not seem to be running within a valid project.")

    options = {}
    if name:
        options["context_name"] = normalize_project_name(name)
    if class_base_name:
        options["class_base_name"] = class_base_name

    options = prompt_for_missing_new_context_options(options)

    context_target_dir = project_source_path / options["context_subdirectory"]

    while (context_target_dir / 'context.py').exists() or (context_target_dir / 'agent.py').exists():
        click.echo(f"Unable to write context at location {context_target_dir} as {context_target_dir / 'context.py'} "
                   f"and/or {context_target_dir / 'agent.py'} already exist.")
        options["context_subdirectory"] = click.prompt(
            "Sub-directory to write context files",
            default=normalize_file_name_component(options["context_name"]),
        )
        context_target_dir = project_source_path / options["context_subdirectory"]

    options['context_target_dir'] = "."
    output_dir = str(context_target_dir.relative_to(project_source_path))

    hatch_config = copy.deepcopy(HATCH_NEW_CONTEXT_CONFIG_FILE_DEFAULTS)
    hatch_context_config = {key.replace("_", "-"): value for key, value in options.items()}
    hatch_config['template']['plugins']['beaker-new-context'] = hatch_context_config

    # Execute hatch new to create the project
    args = [sys.executable, '-m', 'hatch', 'new', options["context_name"], output_dir]
    environ = os.environ.copy()
    with tempfile.NamedTemporaryFile('w') as tempconfig:
        tempconfig.write(toml.dumps(hatch_config))
        tempconfig.flush()
        environ.update({
            "HATCH_CONFIG": tempconfig.name,
        })
        result = subprocess.run(
            args,
            env=environ,
            cwd=project_source_path,
        )
        if result.returncode > 0:
            raise click.ClickException("There was an error setting up your new Beaker project. Please check the output above.")


@context.command(name="list")
def list_contexts():
    """
    List installed contexts.
    """
    from beaker_kernel.lib.context import autodiscover_contexts
    from beaker_kernel.lib import BeakerContext, BeakerAgent
    contexts = autodiscover_contexts()
    if contexts:
        click.echo("Currently installed contexts:\n")
        for context_name, context_cls in contexts.items():
            agent_cls = getattr(context_cls, 'agent_cls', None)
            context_doc = getattr(context_cls, '__doc__', None)
            indent = 4
            output = [
                f"  {context_name}:",
            ]
            if context_doc:
                output.append(
                    # f"    Context docstring:" +
                    f"{' ' * indent}'''\n" +
                    '\n'.join(
                        [
                            (
                                (' ' * indent) +
                                line
                            ) for line in context_doc.splitlines()]
                    ) +
                    f"\n{' ' * indent}'''"
                )
            else:
                output.append(f"{' ' * indent}''' ( docstring not defined ) '''")
            output.extend([
                f"    Context Class:   {context_cls.__module__}.{context_cls.__name__}",
                f"                       ({inspect.getfile(context_cls)})",
            ])
            if agent_cls:
                output.extend([
                f"    Agent Class:     {agent_cls.__module__}.{agent_cls.__name__}",
                f"                       ({inspect.getfile(agent_cls)})",
                # f"      File:            {inspect.getfile(agent_cls)}",

                ])
            output.append("")
            click.echo("\n".join(output))
    else:
        click.echo("No contexts were found. Please check that you are running in the correct environment.")


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
        options["context_subdirectory"] = click.prompt(
            "Sub-directory to write context files",
            default=normalize_file_name_component(defaults.get("context_subdirectory", options["context_name"])),
        )

    return options
