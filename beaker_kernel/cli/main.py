import click
import importlib

from beaker_kernel.lib.autodiscovery import find_mappings


class BeakerCli(click.Group):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


        for _, command_info in find_mappings("commands"):
            group_name = command_info["group_name"]
            module = command_info["module"]
            entry_point = command_info.get("entry_point", "cli_commands")
            try:
                module = importlib.import_module(module)
            except ImportError:
                click.echo(f"Unable to load item {entry_point} from module {module}. Skipping...", err=True)
                continue
            entry = getattr(module, entry_point, None)
            if not entry:
                click.echo(f"Unable to load item {entry_point} from module {module}. Skipping...", err=True)
                continue
            if not isinstance(entry, (click.Command, click.Group)):
                click.echo(f"Entry point {entry_point} in module {module} is not a click Group or Command class. Skipping...", err=True)
            self.add_command(entry, name=group_name)


@click.group(cls=BeakerCli)
def cli():
    """
    CLI Tooling to work with and in Beaker
    """
    pass


from .project import project
from .config import config_group
from .running import dev, notebook
from .context import context
from .subkernel import subkernel

cli.add_command(project)
cli.add_command(config_group)
cli.add_command(context)
cli.add_command(dev)
cli.add_command(notebook)
cli.add_command(subkernel)
