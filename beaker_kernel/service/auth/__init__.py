import contextvars
import os
import hashlib
from dataclasses import dataclass, field
from functools import lru_cache
from traitlets import Unicode, Bool
from typing import Optional

from jupyter_server.auth.authorizer import Authorizer
from jupyter_server.auth.identity import IdentityProvider, User


current_user = contextvars.ContextVar("current_user", default=None)
current_request = contextvars.ContextVar("current_request", default=None)


class BeakerIdentityProvider(IdentityProvider):
    pass


class BeakerAuthorizer(Authorizer):
    pass


@dataclass
class BeakerUser(User):
    home_dir: Optional[str] = field(default=None)

    def __post_init__(self):
        if self.home_dir is None:
            self.home_dir = self._sanitize_homedir(self.username)
        return super().__post_init__()

    @staticmethod
    def _sanitize_homedir(path_string: str):
        # Characters invalid for a path
        invalid_chars = r'<>:"/\|?*@\'' + os.sep
        # Remove any whitespace or invalid characters from the start or end of path.
        stripped_path_string = path_string.strip().strip(invalid_chars)
        # Replace invalid characters with '_'
        sanitized_path = "".join(char if char not in invalid_chars else '_' for char in stripped_path_string)
        full_path = '_'.join((sanitized_path, hashlib.sha1(path_string.encode()).hexdigest()))
        return full_path


@dataclass
class RoleBasedUser(BeakerUser):
    roles: list[str] = field(default_factory=lambda: [])
