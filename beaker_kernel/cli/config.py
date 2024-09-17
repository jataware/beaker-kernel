import os
import toml
from dataclasses import MISSING
from pathlib import Path

import click
import dotenv

from beaker_kernel.lib.config import locate_envfile, locate_config, config, ConfigClass
from beaker_kernel.lib.autodiscovery import LIB_LOCATIONS


SENSITIVE_STR_REPR = "*" * 8


@click.group(name="config")
def config_group():
    """
    Options for viewing and updating configuration settings
    """
    pass


@config_group.command()
def find():
    """
    Locate the configuration file for currently in use
    """
    config_file = locate_config()
    if os.path.isfile(config_file):
        click.echo(f"Configuration location: {config_file}\n")
    else:
        click.echo(f"No configuration file located.\nDefault location is: {config_file}\n")


@config_group.command()
@click.option("--sensitive", "-s", is_flag=True, default=False, type=bool, help="By default, sensitive values are masked. Set this flag to show the actual value.")
def show(sensitive):
    """
    Displays the current Beaker configuration
    """
    config_file: Path|None = locate_config()
    if config_file and config_file.exists():
        config_data = toml.loads(config_file.read_text())
    else:
        config_data = {}
    has_sensitive = False

    click.echo(f"Current Beaker configuration:\n")
    for field_name, field in config.__dataclass_fields__.items():
        config_var: str = field.metadata.get("config_var", None)
        description: str = field.metadata.get("description", "(No description provided)")
        is_sensitive: bool = field.metadata.get("sensitive", False)
        aliases: list[str] = field.metadata.get("aliases", None) or []

        value = getattr(config, field_name)

        exists_in_config_file = False

        vars_to_check = [field_name, *aliases]
        for config_name in vars_to_check:
            if config_name in config_data:
                exists_in_config_file = True
                config_data.pop(config_var)
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
            click.echo("  # (default) - Not defined in config file", nl=False)
        click.echo("\n")

    tools_enabled = config_data.pop('tools_enabled', {})
    if tools_enabled:
        click.echo("The following tools' have are enabled if true or disabled if false:")
        for tool, enabled in tools_enabled.items():
            click.echo(f"  {tool} - {enabled}" )
        click.echo("")

    if config_data:
        click.echo("\nThe following config variables are defined in the configuration file but are not defined "
                   "in the Beaker configuration class:")
        for var_name, value in config_data.items():
            if sensitive:
                click.echo(f"  {var_name}={value}")
            else:
                click.echo(f"  {var_name}={SENSITIVE_STR_REPR}")
        click.echo("")

    if has_sensitive:
        click.echo("# To expose sensitive values, rerun with the -s flag")


@config_group.command()
@click.option("--file", "-f", "envfile", type=click.Path(exists=False))
def update(envfile):
    """
    Iterate through available options, prompting for new or updated values.
    """
    updates = {}

    config_file = locate_config()
    if config_file and config_file.exists():
        config_data = toml.loads(config_file.read_text())
    else:
        config_data = {}

    for field_name, field in config.__dataclass_fields__.items():
        config_var = field.metadata.get("config_var", None)
        description = field.metadata.get("description", "(No description provided)")
        is_sensitive = field.metadata.get("sensitive", False)
        save_default_value = field.metadata.get("save_default_value", False)

        if config_var in config_data:
            default = config_data.get(config_var)
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
        value = click.prompt(prompt, default=default_display)
        was_value_entered = (value != default_display)
        is_value_different = (value != config_data.get(config_var, MISSING))
        if was_value_entered and is_value_different:
            updates[config_var] = value
        elif save_default_value and is_value_different:
            updates[config_var] = default

    if updates:
        click.echo("Updated values:")
        click.echo(f"\n".join(f"  {varname}={value}" for varname, value in updates.items()))
        approval = click.prompt(f"Save above values to file {config_file}?", default="y", type=bool)
        if isinstance(approval, bool) and approval:
            click.echo("Saving...")
            config.update(updates, config_file)
            click.echo("Done.")
        else:
            click.echo("Aborting without saving.")
    else:
        click.echo("No updates detected.")
