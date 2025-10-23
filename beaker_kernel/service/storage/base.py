import os
import os.path
from dataclasses import dataclass
from typing import Any

import traitlets

from jupyter_server.services.contents.manager import ContentsManager
from jupyter_server.services.contents.largefilemanager import AsyncLargeFileManager
from beaker_kernel.service.auth import current_user, BeakerUser, BeakerAuthorizer, BeakerIdentityProvider


def with_hidden_files(func):
    """Decorator to temporarily enable hidden files during a method call."""
    async def wrapper(self, *args, **kwargs):
        orig_allow_hidden = self.contents_manager.allow_hidden
        self.contents_manager.allow_hidden = True
        try:
            result = await func(self, *args, **kwargs)
        finally:
            self.contents_manager.allow_hidden = orig_allow_hidden
        return result
    return wrapper


class BaseBeakerContentsManager(ContentsManager):
    pass

class BeakerLocalContentsManager(AsyncLargeFileManager, BaseBeakerContentsManager):
    def _get_os_path(self, path):
        """Override path resolution to use user-specific home directory.

        Parameters
        ----------
        path : str
            Relative path to resolve

        Returns
        -------
        str
            Absolute path within user's home directory
        """
        user: BeakerUser = current_user.get()
        if user:
            path = os.path.join(user.home_dir, path)
        return super()._get_os_path(path)

    async def _notebook_model(self, path, content=True, require_hash=False):
        """
        Override to include session_id in notebook model.
        """
        model = await super()._notebook_model(path, True, require_hash)
        metadata = model.get("content", {}).get("metadata", {})
        model["session_id"] = metadata.get("beaker", {}).get("session_id", None)
        if not content:
            del model["content"]
            del model["format"]
        return model


class BeakerStorageManager(BaseBeakerContentsManager):
    pass
