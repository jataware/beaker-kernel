import importlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import MISSING

import click
import dotenv

from beaker_kernel.lib.config import config as beaker_config
from beaker_kernel.lib.autodiscovery import LIB_LOCATIONS


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
    from beaker_kernel.server.main import BeakerJupyterApp
    try:
        # BeakerJupyterApp.launch_instance(argv=[jupyter_args])
        app = BeakerJupyterApp.initialize_server(argv=jupyter_args)
        app.start()
    finally:
        pass


@cli.group(name="dev", invoke_without_command=True)
@click.pass_context
def dev(ctx):
    # Don't run if we are running watch
    if ctx.invoked_subcommand is None:
        # Invoke watch as default action
        watch.invoke(ctx)
        return


@dev.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("jupyter_args", nargs=-1, type=click.UNPROCESSED)
def serve(jupyter_args):
    from beaker_kernel.server.dev import DevBeakerJupyterApp

    try:
        app = DevBeakerJupyterApp.initialize_server(argv=jupyter_args)
        app.start()
    finally:
        pass


@dev.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.option("--extra_dir", multiple=True)
@click.argument("jupyter_args", nargs=-1, type=click.UNPROCESSED)
def watch(extra_dir=None, jupyter_args=None):
    from beaker_kernel.server.dev import create_observer
    app_subprocess = None

    def restart():
        click.echo(" *** Restarting service *** \n")
        app_subprocess.terminate()

    observer = create_observer(extra_dir, restart)
    try:
        while True:
            try:
                app_subprocess = subprocess.Popen([
                        sys.executable,
                        sys.argv[0], "dev", "serve", *jupyter_args],
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
            app_subprocess.kill()
        observer.unschedule_all()
        observer.stop()
        del observer


@cli.command()
def config():
    sensitive_str = "*" * 8
    envfile = dotenv.find_dotenv()
    updates = {}
    if envfile:
        envfile = os.path.abspath(envfile)
    else:
        envfile = os.path.abspath(os.path.join(os.path.curdir, ".env"))
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
            default_display = sensitive_str
        else:
            default_display = default

        prompt = f"""
Please enter the value for configuration option {field_name} (environment variable {env_var})
Description: {description}

{field_name}"""
        value = click.prompt(prompt, default=default_display,)
        if value == sensitive_str:
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
                dotenv.set_key(envfile, varname, value)
            click.echo("Done.")
        else:
            click.echo("Aborting without saving.")
    else:
        click.echo("No updates detected.")
