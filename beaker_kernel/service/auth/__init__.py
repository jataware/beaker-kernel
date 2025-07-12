import contextvars
import inspect
import os
import hashlib
import logging
from dataclasses import dataclass, field
from functools import lru_cache, update_wrapper, wraps
from traitlets import Unicode, Bool
from typing import Optional

from jupyter_server.auth.authorizer import Authorizer
from jupyter_server.auth.identity import IdentityProvider, User
from tornado import web


current_user = contextvars.ContextVar("current_user", default=None)
current_request = contextvars.ContextVar("current_request", default=None)


class BeakerIdentityProvider(IdentityProvider):

    beaker_kernel_header = Unicode(
        "X-AUTH-BEAKER",
        config=True,
    )

    async def _is_authorized_beaker_kernel(self, handler: web.RequestHandler):
        auth_token = handler.request.headers.get(self.beaker_kernel_header, None)
        if not auth_token:
            return False

        try:
            preamble, kernel_id, nonce, hash_value = auth_token.split(':')
            if preamble != "beaker-kernel" or not kernel_id or not hash_value:
                return False
            kernel = handler.kernel_manager.get_kernel(kernel_id)
            key = kernel.session.key.decode()

            payload = f"{kernel_id}{nonce}{key}".encode()
            reconstructed_hash_value = hashlib.md5(payload).hexdigest()
            valid = reconstructed_hash_value == hash_value
            return valid

        except Exception as err:
            logging.error(err)
            return False


    @classmethod
    def beaker_kernel_auth_wrapper(cls, fn):
        @wraps(fn)
        async def get_user(self: BeakerIdentityProvider, handler: web.RequestHandler):
            is_beaker = await self._is_authorized_beaker_kernel(handler)
            if is_beaker:
                handler._token_authenticated = True
                return RoleBasedUser(
                    username="beaker_kernel_",
                    name="Beaker Kernel",
                    roles=["admin"],
                )
            else:
                result = fn(self, handler)
                if inspect.isawaitable(result):
                    result = await result
                return result
        return get_user

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        get_user = cls.beaker_kernel_auth_wrapper(cls.get_user)
        update_wrapper(get_user, cls.get_user)
        cls.get_user = get_user


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
