import json
import logging
import os

from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.extension.handler import ExtensionHandlerMixin
from jupyter_server.services.sessions.sessionmanager import SessionManager
from jupyter_server.services.kernels.kernelmanager import AsyncMappingKernelManager

from beaker_kernel.lib.autodiscovery import autodiscover
from beaker_kernel.lib.app import BeakerApp
from beaker_kernel.lib.context import BeakerContext
from beaker_kernel.lib.subkernel import BeakerSubkernel
from beaker_kernel.lib.agent_tasks import summarize
from beaker_kernel.lib.config import config, locate_config, Config, Table, Choice, recursiveOptionalUpdate, reset_config
from beaker_kernel.service import admin_utils

logger = logging.getLogger(__name__)

from abc import ABC, abstractmethod

from functools import lru_cache

context_cache = None

@lru_cache
def get_context(context_slug: str):
    global context_cache
    if context_cache is None:
        context_cache = autodiscover("contexts")
    return context_cache.get(context_slug)


# Resource Handlers

class ResourceHandler(ABC):
    KEY: str

    @abstractmethod
    async def get(self, context_slug, integration_id, resource_id=None):
        pass

    @abstractmethod
    async def new(self, context_slug, integration_id, payload):
        pass

    @abstractmethod
    async def replace(self, context_slug, integration_id, resource_id, payload):
        pass

    @abstractmethod
    async def delete(self, context_slug, integration_id, resource_id):
        pass


class FileResourceHandler(ResourceHandler):
    KEY="file"

    async def get(self, context_slug, integration_id, resource_id=None):
        pass

    async def new(self, context_slug, integration_id, payload):
        return await super().new(integration_id, payload)

    async def replace(self, context_slug, integration_id, resource_id, payload):
        return await super().replace(integration_id, resource_id, payload)

    async def delete(self, context_slug, integration_id, resource_id):
        return await super().delete(integration_id, resource_id)


class ExampleResourceHandler(ResourceHandler):
    KEY="example"

    async def get(self, context_slug, integration_id, resource_id=None):
        pass

    async def new(self, context_slug, integration_id, payload):
        return await super().new(context_slug, integration_id, payload)

    async def replace(self, context_slug, integration_id, resource_id, payload):
        return await super().replace(context_slug, integration_id, resource_id, payload)

    async def delete(self, context_slug, integration_id, resource_id):
        return await super().delete(context_slug, integration_id, resource_id)


Resources: list[ResourceHandler] = [
    FileResourceHandler,
    ExampleResourceHandler,
]

ResourceMap = {
    cls.KEY: cls for cls in Resources
}


class BeakerAPIMixin:
    session_manager: SessionManager
    kernel_manager: AsyncMappingKernelManager

    async def get_session_context_info(self, session_id: str):
        try:
            session = await self.session_manager.get_session(name=session_id)
        except Exception as err:
            return None
        kernel = self.kernel_manager.get_kernel(session["kernel"]["id"])
        if not kernel:
            return None

        if os.path.exists(kernel.connection_file):
            with open(kernel.connection_file) as f:
                session_info = json.load(f)
        else:
            return None
        context_info = session_info["context"]
        # context_cls = autodiscover("contexts").get(context_info["name"], None)
        client = kernel.client()
        msg = client.session.send(
            stream=client.shell_channel.socket,
            msg_or_type="beaker_session_info_request",
            content={},
            track=True,
            metadata=None,
        )
        result = await client.get_shell_msg(msg_id=msg["msg_id"])
        return result.get("content", {}).get("result", None)


# Integration Handler

class IntegrationHandler(BeakerAPIMixin, ExtensionHandlerMixin, JupyterHandler):
    """
    Handles fetching and adding integrations.
    """

    async def head(self):
        pass

    async def get(self, session_id=None, integration_id=None):
        session_info = await self.get_session_context_info(session_id=session_id)
        context = session_info
        self.log.warning(context)
        if integration_id is None:
            integration_list = context()
        else:
            # Return details of single integration
            pass

    async def post(self, integration_id):
        # Create new/replace integration
        pass


class IntegrationResourceHandler(ExtensionHandlerMixin, JupyterHandler):
    """
    Handles fetching and adding resources belonging to an integration.
    """

    async def head(self, session_id=None, context_slug=None, integration_id=None, resource_type=None, resource_id=None):
        pass

    async def get(self, session_id=None, context_slug=None, integration_id=None, resource_type=None, resource_id=None):
        resource_cls = ResourceMap.get(resource_type, None)
        pass

    async def post(self, session_id=None, context_slug=None, integration_id=None, resource_type=None, resource_id=None):
        resource_cls = ResourceMap.get(resource_type, None)
        pass


handlers = [
    (r'integrations/(?P<session_id>[\w\d-]+)/?(?P<integration_id>[\w\d-]+)?', IntegrationHandler),
    (r'integrations/(?P<session_id>[\w\d-]+)/(?P<integration_id>[\w\d-]+)/(?P<resource_type>\w+)/?(?P<resource_id>\w+)?', IntegrationResourceHandler),
]
