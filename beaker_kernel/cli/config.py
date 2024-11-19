import os
import toml
from dataclasses import MISSING, is_dataclass
from pathlib import Path

import click
import dotenv

from beaker_kernel.lib.config import locate_envfile, locate_config, config, ConfigClass, Table
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


def _print_config_obj(obj, sensitive=False, obj_type=None, metadata=None, indent_level=0):
    from typing import get_origin, get_args
    description: str = metadata is not None and metadata.get("description", None)
    if obj_type is None:
        obj_type = obj.__class__
    if is_dataclass(obj) or is_dataclass(obj_type):
        if description:
            click.echo(f"\n{'  ' * indent_level}# {description}")
        indent_level += 1
        for field_name, field in obj_type.__dataclass_fields__.items():
            metadata = field.metadata
            aliases: list[str] = field.metadata.get("aliases", None) or []

            if is_dataclass(obj):
                value = getattr(obj, field_name)
            else:
                value = obj.get(field_name)

            vars_to_check = [field_name, *aliases]
            for config_name in vars_to_check:
                if config_name in obj:
                    obj.pop(config_name)
                    break

            click.echo(f"{'  ' * indent_level}{field_name}: ", nl=False)
            _print_config_obj(value, sensitive=sensitive, obj_type=field.type, metadata=metadata, indent_level=indent_level + 1)
    elif isinstance(obj, Table) or (get_origin(obj_type) is not None and issubclass(get_origin(obj_type), Table)):
        if description:
            click.echo(f"\n{'  ' * indent_level}# {description}")
        for key, value in obj.items():
            click.echo(f"{'  ' * (indent_level)}{key}: ", nl=True)
            _print_config_obj(value, sensitive=sensitive, obj_type=get_args(obj_type)[0], indent_level=indent_level+1)
    else:
        if description:
            click.echo(f"{'  ' * indent_level}# {description}")
        is_sensitive: bool = metadata is not None and metadata.get("sensitive", False) or False
        if is_sensitive and not sensitive:
            if obj:
                display_value = SENSITIVE_STR_REPR  # rerun with -s flag to display value
            else:
                display_value = '(undefined)'
        elif isinstance(obj, str) and obj == "":
            display_value = '"" (empty string)'
        else:
            display_value = obj
        click.echo(f"{'  ' * indent_level}{display_value}")



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

    click.echo(f"Current Beaker configuration:")
    _print_config_obj(config_data, sensitive=sensitive, obj_type=ConfigClass, indent_level=0)

    if not sensitive:
        click.echo("\n# To expose sensitive values, rerun with the -s flag")

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
