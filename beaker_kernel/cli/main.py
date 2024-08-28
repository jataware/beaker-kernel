import importlib
import json
import os

import click
import dotenv

from beaker_kernel.lib.autodiscovery import LIB_LOCATIONS


# try:
#     dotenv.load_dotenv()
# except Exception as e:
#     pass

class BeakerCli(click.Group):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        subpackages = {}
        for location in LIB_LOCATIONS:
            commands_dir = os.path.join(location, "commands")
            if os.path.exists(commands_dir):
                for command_json_file in os.listdir(commands_dir):
                    if not command_json_file.endswith(".json"):
                        continue
                    command_json_file_fullpath = os.path.join(commands_dir, command_json_file)
                    with open(os.path.join(commands_dir, command_json_file)) as fh:
                        try:
                            command_info = json.load(fh)
                        except json.JSONDecodeError as err:
                            click.echo(f"Package {command_json_file_fullpath} does not match expected format. Skipping...", err=True)
                            continue
                    if "group_name" in command_info and "module" in command_info:
                        subpackages[command_info["group_name"]] = command_info
                    else:
                        click.echo(f"Package {command_json_file_fullpath} does not match expected format. Skipping...", err=True)
                        continue

        for group_name, command_info in subpackages.items():
            module = command_info["module"]
            entry_point = command_info.get("entry_point", "cli_commands")
            module = importlib.import_module(module)
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
# cli.add_command(context)
cli.add_command(dev)
cli.add_command(notebook)
# cli.add_command(subkernel)
