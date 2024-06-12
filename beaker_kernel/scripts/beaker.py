import importlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import MISSING

import click
import dotenv
import webbrowser

from beaker_kernel.lib.config import locate_envfile, config as beaker_config
from beaker_kernel.lib.autodiscovery import LIB_LOCATIONS


SENSITIVE_STR_REPR = "*" * 8


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


@cli.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("jupyter_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def notebook(ctx, jupyter_args):
    """
    Start Beaker in local mode and opens a notebook.
    """
    from beaker_kernel.server.main import BeakerJupyterApp
    try:
        app = BeakerJupyterApp.initialize_server(argv=jupyter_args)
        webbrowser.open(app.public_url)
        app.start()
    finally:
        app.stop()


@cli.group(name="dev", invoke_without_command=True)
@click.option("--no-open-notebook", "-n", is_flag=True, default=False, type=bool, help="Prevent opening the notebook in a webbrowser.")
@click.pass_context
def dev(ctx: click.Context, no_open_notebook):
    """
    Start Beaker server in development mode. (Subcommands available)
    """
    # Don't run if we are running watch
    if ctx.invoked_subcommand is None:
        # Invert the default behavior around opening the notebook as `watch` has an opposite default.
        ctx.params["open_notebook"] = not ctx.params.pop("no_open_notebook")
        # Invoke watch as default action
        watch.invoke(ctx)
        return


@dev.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("jupyter_args", nargs=-1, type=click.UNPROCESSED)
@click.option("--open-notebook", "-n", is_flag=True, default=False, type=bool, help="Open a notebook in a webbrowser.")
def serve(jupyter_args, open_notebook):
    from beaker_kernel.server.dev import DevBeakerJupyterApp

    try:
        app = DevBeakerJupyterApp.initialize_server(argv=jupyter_args)
        if open_notebook:
            webbrowser.open(app.public_url)
        app.start()
    finally:
        app.stop()


@dev.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.option("--extra_dir", multiple=True)
@click.option("--open-notebook", "-n", is_flag=True, default=False, type=bool, help="Open a notebook in a webbrowser.")
@click.argument("jupyter_args", nargs=-1, type=click.UNPROCESSED)
def watch(extra_dir=None, open_notebook=None, jupyter_args=None):
    from beaker_kernel.server.dev import create_observer
    app_subprocess = None
    jupyter_args = jupyter_args or []

    def restart():
        click.echo(" *** Restarting service *** \n")
        app_subprocess.terminate()

    observer = create_observer(extra_dir, restart)
    try:
        while True:
            try:
                args = [
                    sys.executable,
                    sys.argv[0], "dev", "serve", *jupyter_args
                ]
                if open_notebook:
                    args.append("--open-notebook")
                app_subprocess = subprocess.Popen(
                    args,
                    env=os.environ
                )
                app_subprocess.wait()
            except (InterruptedError, KeyboardInterrupt, EOFError) as err:
                click.echo("y")
                click.echo("Shutting down...")
                break
    finally:
        if app_subprocess:
            click.echo("Cleaning up...")
            app_subprocess.terminate()
        observer.unschedule_all()
        observer.stop()
        del observer


@cli.group()
def config():
    """
    Options for viewing and updating configuration settings
    """
    pass


@config.command()
def find():
    """
    Locate the configuration file for currently in use
    """
    envfile = locate_envfile()
    if os.path.isfile(envfile):
        click.echo(f"Configuration location: {envfile}\n")
    else:
        click.echo(f"No configuration file located.\nDefault location is: {envfile}\n")


@config.command()
@click.option("--sensitive", "-s", is_flag=True, default=False, type=bool, help="By default, sensitive values are masked. Set this flag to show the actual value.")
def show(sensitive):
    """
    Displays the current Beaker configuration
    """
    envfile: str = locate_envfile()
    if os.path.isfile(envfile):
        dotenv_config = dotenv.dotenv_values(envfile)
    else:
        dotenv_config = {}
    has_sensitive = False

    click.echo(f"Current Beaker configuration:\n")
    for field_name, field in beaker_config.__dataclass_fields__.items():
        env_var: str = field.metadata.get("env_var", None)
        description: str = field.metadata.get("description", "(No description provided)")
        is_sensitive: bool = field.metadata.get("sensitive", False)
        aliases: list[str] = field.metadata.get("aliases", None) or []

        value = getattr(beaker_config, field_name)

        exists_in_config_file = False
        env_vars_to_check = [env_var, *aliases]
        for env_var in env_vars_to_check:
            if env_var in dotenv_config:
                exists_in_config_file = True
                dotenv_config.pop(env_var)
                break

        if is_sensitive and not sensitive:
            if value:
                display_value = SENSITIVE_STR_REPR  # rerun with -s flag to display value
            else:
                display_value = '(undefined)'
            has_sensitive = True
        else:
            display_value = value

        click.echo(f"# {field_name}: {description}")
        click.echo(f"{field_name}={display_value}", nl= False)
        if not exists_in_config_file:
            click.echo("  # default  not defined in config file", nl=False)
        click.echo("\n")

    if dotenv_config:
        click.echo("\nThe following environment variables are defined in the configuration file but not defined in the "
                   "Beaker configuration:")
        for var_name, value in dotenv_config.items():
            if sensitive:
                click.echo(f"  {var_name}={value}")
            else:
                click.echo(f"  {var_name}={SENSITIVE_STR_REPR}")
        click.echo("")

    if has_sensitive:
        click.echo("# To expose sensitive values, rerun with the -s flag")


@config.command()
@click.option("--file", "-f", "envfile", type=click.Path(exists=False))
def update(envfile):
    """
    Iterate through available options, prompting for new or updated values.
    """
    updates = {}
    if envfile is None:
        envfile = locate_envfile()
    envfile_exists = os.path.isfile(envfile)
    if envfile_exists:
        dotenv_config = dotenv.dotenv_values(envfile)
    else:
        dotenv_config = {}

    for field_name, field in beaker_config.__dataclass_fields__.items():
        env_var = field.metadata.get("env_var", None)
        description = field.metadata.get("description", "(No description provided)")
        is_sensitive = field.metadata.get("sensitive", False)
        if not env_var:
            click.echo(f"Skipping config option '{field_name} as no environment variable has been defined.")
        if env_var in dotenv_config:
            default = dotenv_config.get(env_var)
        else:
            if field.default is not MISSING:
                default = field.default
            elif field.default_factory is not MISSING:
                default = field.default_factory()
            else:
                default = MISSING

        if is_sensitive and default:
            default_display = SENSITIVE_STR_REPR
        else:
            default_display = default

        prompt = f"""
Please enter the value for configuration option {field_name}:
Description: {description}

{field_name}"""
        value = click.prompt(prompt, default=default_display,)
        if value == SENSITIVE_STR_REPR:
            value = default
        if value != dotenv_config.get(env_var, MISSING):
            updates[env_var] = value

    if updates:
        click.echo("Updated values:")
        click.echo(f"\n".join(f"  {varname}={value}" for varname, value in updates.items()))
        approval = click.prompt(f"Save above values to file {envfile}?", default="y", type=bool)
        if isinstance(approval, bool) and approval:
            click.echo("Saving...")
            for varname, value in updates.items():
                dotenv.set_key(envfile, varname, value, quote_mode="never")
            click.echo("Done.")
        else:
            click.echo("Aborting without saving.")
    else:
        click.echo("No updates detected.")
