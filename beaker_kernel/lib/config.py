import binascii
import os
import re
from dataclasses import dataclass, field, MISSING
from typing_extensions import Self

from dotenv import load_dotenv

load_dotenv()

def new_token():
    return binascii.hexlify(os.urandom(24)).decode("ascii")


def envfield(
    env_var: str,
    description: str,
    *,
    default = MISSING,
    default_factory = MISSING,
    sensitive: bool = False
):
    kwargs = {
        "metadata": {
            "env_var": env_var,
            "description": description,
            "sensitive": sensitive,
        }
    }
    env_value = os.getenv(env_var, default=MISSING)
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

field()

@dataclass
class ConfigClass:
    jupyter_server: str = envfield(
        "JUPYTER_SERVER",
        "URL of Jupyter or Beaker Server which manages subkernels.",
        default="http://localhost:8888",
    )
    jupyter_token: str = envfield(
        "JUPYTER_TOKEN",
        "Token to use when communicating with the Jupyter or Beaker server.",
        default_factory=new_token,
    )
    archytas_auth: str | None = envfield(
        "OPENAI_API_KEY",
        "API key used for authenticating to the LLM service, if required.",
        default=None,
        sensitive=True,
    )


config = ConfigClass()
