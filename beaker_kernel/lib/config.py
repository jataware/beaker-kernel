import binascii
import os
import re
from dataclasses import dataclass, field, MISSING
from typing_extensions import Self

from dotenv import load_dotenv, find_dotenv

load_dotenv()

def new_token():
    return binascii.hexlify(os.urandom(24)).decode("ascii")


def envfield(
    env_var: str,
    description: str,
    *,
    default = MISSING,
    default_factory = MISSING,
    sensitive: bool = False,
    aliases: list[str] = None
):
    kwargs = {
        "metadata": {
            "env_var": env_var,
            "description": description,
            "sensitive": sensitive,
            "aliases": aliases,
        }
    }
    # Get value if defined
    env_value = os.getenv(env_var, default=MISSING)

    # If not defined and aliases are defined, check the aliases
    if env_value is MISSING and isinstance(aliases, list):
        for alias in aliases:
            alias_value = os.getenv(alias, default=MISSING)
            if alias_value is not MISSING:
                env_value = alias_value
                break

    # Fill in default definitions based on above findings and arguments
    if env_value is not MISSING:
        def factory():
            return env_value
        kwargs["default_factory"] = factory
    elif default is not MISSING:
        kwargs["default"] = default
    elif default_factory is not MISSING:
        kwargs["default_factory"] = default_factory
    return field(
        **kwargs
    )


@dataclass
class ConfigClass:
    JUPYTER_SERVER: str = envfield(
        "JUPYTER_SERVER",
        "URL of Jupyter or Beaker Server which manages subkernels.",
        default="http://localhost:8888",
    )
    JUPYTER_TOKEN: str = envfield(
        "JUPYTER_TOKEN",
        "Token to use when communicating with the Jupyter or Beaker server.",
        default_factory=new_token,
    )
    LLM_SERVICE_TOKEN: str | None = envfield(
        "LLM_SERVICE_TOKEN",
        "API key used for authenticating to the LLM service, if required.",
        default=None,
        sensitive=True,
        aliases=["OPENAI_API_KEY"]
    )


config = ConfigClass()


def locate_envfile() -> str:
    """
    Returns the location of the used envfile or default location is no envfile found
    """
    envfile = find_dotenv()
    if envfile:
        envfile = os.path.abspath(envfile)
    else:
        envfile = os.path.abspath(os.path.join(os.path.curdir, ".env"))
    return envfile
