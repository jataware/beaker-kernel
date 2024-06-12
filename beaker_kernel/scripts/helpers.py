from pathlib import Path
import hashlib


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
