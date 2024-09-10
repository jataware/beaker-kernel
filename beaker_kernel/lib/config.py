import binascii
import dotenv
import os
import re
import toml
from dataclasses import dataclass, field, MISSING
from pathlib import Path
from typing_extensions import Self


CONFIG_FILE_SEARCH_LOCATIONS = [  # (path, filename, check_parent_paths, default)
    (Path.cwd(), ".beaker.conf", True, False),
    (Path("~/.config").expanduser(), 'beaker.conf', False, True),
    (Path("~").expanduser(), '.beaker.conf', False, False),
]


def new_token():
    return binascii.hexlify(os.urandom(24)).decode("ascii")


def envfield(
    config_var: str,
    description: str,
    *,
    default = MISSING,
    default_factory = MISSING,
    sensitive: bool = False,
    aliases: list[str] = None,
    save_default_value: bool = False,
):
    def dynamic_factory():
        # Get value if defined
        env_value = os.getenv(config_var, default=MISSING)

        # If not defined and aliases are defined, check the aliases
        if env_value is MISSING and isinstance(aliases, list):
            for alias in aliases:
                alias_value = os.getenv(alias, default=MISSING)
                if alias_value is not MISSING:
                    env_value = alias_value
                    break

        # Fill in default definitions based on above findings and arguments
        if env_value is not MISSING:
            return env_value
        elif default is not MISSING:
            return default
        elif default_factory is not MISSING:
            return default_factory()

    return field(
        metadata={
            "config_var": config_var,
            "description": description,
            "sensitive": sensitive,
            "aliases": aliases,
            "save_default_value": save_default_value,
        },
        default_factory=dynamic_factory,
    )

JUPYTER_SERVER_DEFAULT = "http://localhost:8888"


@dataclass
class ConfigClass:
    JUPYTER_SERVER: str = envfield(
        "JUPYTER_SERVER",
        "URL of Jupyter or Beaker Server which manages subkernels.",
        default=JUPYTER_SERVER_DEFAULT,
        save_default_value=False,
    )
    JUPYTER_TOKEN: str = envfield(
        "JUPYTER_TOKEN",
        "Token to use when communicating with the Jupyter or Beaker server.",
        default_factory=new_token,
        save_default_value=False,
    )
    LLM_SERVICE_MODEL: str = envfield(
        "LLM_SERVICE_MODEL",
        "Name of LLM model to use.",
        default="gpt-4o",
        sensitive=False,
        save_default_value=True,
    )
    LLM_SERVICE_TOKEN: str | None = envfield(
        "LLM_SERVICE_TOKEN",
        "API key used for authenticating to the LLM service, if required.",
        default=None,
        sensitive=True,
        aliases=["OPENAI_API_KEY"],
    )

    @classmethod
    def from_config_file(cls, config_file_path: Path|str|None = None, load_dotenv=True):
        config_file = locate_config(start_path=config_file_path)
        if config_file and config_file.exists():
            config_data = toml.loads(config_file.read_text())
        else:
            config_data = {}

        if load_dotenv and config_data.get("LOAD_DOTENV", True):
            # Ensure that the latest envfile is loaded
            env_file = locate_envfile()
            dotenv.load_dotenv(dotenv_path=env_file)

        # Create instance, passing in only options that are defined as fields
        return cls(**{
            option: value
            for option, value in config_data.items()
            if option in cls.__dataclass_fields__
        })

    def update(self, updates: dict, config_file_path: Path|str|None = None):
        if config_file_path is None:
            config_file = locate_config(start_path=config_file_path)
        else:
            config_file = Path(config_file_path)
        if config_file.exists():
            config_data = toml.loads(config_file.read_text())
        else:
            config_data = {}
        print(f"Writing to {config_file}")
        for var_name, value in updates.items():
            config_data[var_name] = value
        config_file.write_text(toml.dumps(config_data))


class Config(ConfigClass):
    """Lazy loading wrapper around ConfigClass"""
    config_obj: ConfigClass | None

    def __init__(self) -> None:
        self.config_obj = None

    def __getattr__(self, name: str):
        if name in (['__dataclass_fields__', '__dataclass_params__'] + list(ConfigClass.__dataclass_fields__.keys())):
            if not self.config_obj:
                self.config_obj = ConfigClass.from_config_file()
            return getattr(self.config_obj, name)
        raise AttributeError

config = Config()


def reset_config():
    config.config_obj = None


def locate_config(start_path: str|Path|None = None) -> Path | None:
    """
    Returns the location of the used Beaker config file or default location is no config file is found
    """
    # Avoid circular imports
    from .utils import find_file_along_path

    default_location = None
    if start_path is not None:
        locations = [(Path(start_path), '.beaker.conf', True, True)] + CONFIG_FILE_SEARCH_LOCATIONS
    else:
        locations = CONFIG_FILE_SEARCH_LOCATIONS
    for path, filename, recurse, is_default in locations:
        if recurse:
            location = find_file_along_path(filename, path)
        else:
            location = Path(path) / filename
        if isinstance(location, Path):
            if location.exists():
                return location
            if is_default and default_location is None:
                default_location = location
    return default_location


def locate_envfile() -> str:
    """
    Returns the location of the used envfile or default location is no envfile found
    """
    envfile = dotenv.find_dotenv()
    if envfile:
        envfile = os.path.abspath(envfile)
    else:
        envfile = os.path.abspath(os.path.join(os.path.curdir, ".env"))
    return envfile
