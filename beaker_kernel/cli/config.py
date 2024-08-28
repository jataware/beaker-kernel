import os
from dataclasses import MISSING

import click
import dotenv

from beaker_kernel.lib.config import locate_envfile, config
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
    envfile = locate_envfile()
    if os.path.isfile(envfile):
        click.echo(f"Configuration location: {envfile}\n")
    else:
        click.echo(f"No configuration file located.\nDefault location is: {envfile}\n")


@config_group.command()
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
    for field_name, field in config.__dataclass_fields__.items():
        env_var: str = field.metadata.get("env_var", None)
        description: str = field.metadata.get("description", "(No description provided)")
        is_sensitive: bool = field.metadata.get("sensitive", False)
        aliases: list[str] = field.metadata.get("aliases", None) or []

        value = getattr(config, field_name)

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


@config_group.command()
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

    for field_name, field in config.__dataclass_fields__.items():
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
