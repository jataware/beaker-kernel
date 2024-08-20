import click
import dotenv
import hashlib
import sys
from pathlib import Path
from functools import wraps

from beaker_kernel.lib.config import locate_envfile, reset_config

def find_pyproject_file() -> Path | None:
    cwd = Path.cwd()
    for path in [cwd, *cwd.parents]:
        potential_file = path / "pyproject.toml"
        if potential_file.is_file():
            return potential_file
    return None


def calculate_content_hash(
    content: str,
    hash_algo: str = "sha256"
) -> str:
    if isinstance(content, str):
        content = content.encode()
    hash_obj = hashlib.new(hash_algo, data=content)
    return str(hash_obj.hexdigest())

def ensure_config(fn):
    @wraps(fn)
    def _inner(*args, **kwargs):
        # Import update inside wrapping function to prevent circular imports. Could fail in outer file and in top-level
        # decorator.
        from .config import update

        ctx = click.get_current_context()

        if not Path(locate_envfile()).exists():
            click.echo("Looks like you haven't created a configuration yet. Let's do that now...")
            sys.stdout.flush()
            ctx.invoke(update)
            # Ensure config is reset before running function, to ensure that we don't use the default values.
            reset_config()

        fn(*args, **kwargs)

    return _inner
