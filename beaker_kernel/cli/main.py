import click
import importlib

from beaker_kernel.lib.autodiscovery import find_mappings


class BeakerCli(click.Group):
    subcommands: dict[str, click.Command | click.Group]
    apps: dict[str, str]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.subcommands = {}
        self.apps = {}

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
            self.subcommands[group_name] = entry

        for _, app_info in find_mappings("apps"):
            app_name = app_info["slug"]
            package = app_info["package"]
            class_name = app_info["class_name"]
            app_import_str = f"{package}.{class_name}"
            try:
                module = importlib.import_module(package)
                cls = getattr(module, class_name, None)
            except ImportError:
                cls = None
            if cls is None:
                continue
            self.apps[app_name] = app_import_str

    def list_commands(self, ctx):
        commands = super().list_commands(ctx)
        commands.extend(self.subcommands.keys())
        commands.extend(self.apps.keys())
        return commands

    def get_command(self, ctx, cmd_name):
        if cmd_name in self.subcommands:
            return self.subcommands[cmd_name]
        elif cmd_name in self.apps:
            from .app import build_app_command
            import_str = self.apps[cmd_name]
            return build_app_command(cmd_name, import_str)
        else:
            return super().get_command(ctx, cmd_name)

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
from .app import app

cli.add_command(project)
cli.add_command(config_group)
cli.add_command(context)
cli.add_command(dev)
cli.add_command(notebook)
cli.add_command(subkernel)
cli.add_command(app)
