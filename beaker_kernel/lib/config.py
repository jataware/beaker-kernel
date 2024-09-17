import binascii
import dotenv
import logging
import os
import toml
from dataclasses import dataclass, field, MISSING
from pathlib import Path
from typing import Callable, Any
from typing_extensions import Self

logger = logging.getLogger(__name__)


CONFIG_FILE_SEARCH_LOCATIONS = [  # (path, filename, check_parent_paths, default)
    (Path.cwd(), ".beaker.conf", True, False),
    (Path("~/.config").expanduser(), 'beaker.conf', False, True),
    (Path("~").expanduser(), '.beaker.conf', False, False),
]


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


def new_token():
    return binascii.hexlify(os.urandom(24)).decode("ascii")


def normalize_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        # Hard-coded "True" values. Anything else is False.
        return value.lower() in ('true', 'y', 't', '1')
    else:
        return False


def envfield(
    config_var: str,
    description: str,
    *,
    default = MISSING,
    default_factory = MISSING,
    sensitive: bool = False,
    aliases: list[str] = None,
    save_default_value: bool = False,
    normalize_function: Callable[[Any], Any] = MISSING
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
            value = env_value
        elif default is not MISSING:
            value = default
        elif default_factory is not MISSING:
            value = default_factory()

        if normalize_function is not MISSING:
            value = normalize_function(value)
        return value

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
    ENABLE_CHECKPOINTS: bool = envfield(
        "ENABLE_CHECKPOINTS",
        "Flag as to whether checkpoints are enabled or not.",
        default=True,
        sensitive=False,
        normalize_function=normalize_bool,
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
        instance = cls(**{
            option: value
            for option, value in config_data.items()
            if option in cls.__dataclass_fields__ and not option.startswith('_')
        })

        instance._tools_enabled = config_data.get('tools_enabled', {})
        return instance

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
            self.__dict__[var_name] = value
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

    @property
    def tools_enabled(self) -> dict[str, bool]:
        return getattr(self.config_obj, '_tools_enabled', {})

config = Config()


def reset_config():
    config.config_obj = None
