import json
import logging
import os
import typing
import asyncio

from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.extension.handler import ExtensionHandlerMixin
from jupyter_server.services.kernels.kernelmanager import AsyncMappingKernelManager
from jupyter_server.services.sessions.sessionmanager import SessionManager

from beaker_kernel.lib.agent_tasks import summarize
from beaker_kernel.lib.app import BeakerApp
from beaker_kernel.lib.autodiscovery import autodiscover
from beaker_kernel.lib.config import Choice, Config, Table, config, locate_config, recursiveOptionalUpdate, reset_config
from beaker_kernel.lib.context import BeakerContext
from beaker_kernel.lib.subkernel import BeakerSubkernel
from beaker_kernel.lib.utils import ensure_async
from beaker_kernel.service import admin_utils

import tornado

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
    async def get(self, integration_id, resource_id=None):
        pass

    @abstractmethod
    async def new(self, integration_id, payload):
        pass

    @abstractmethod
    async def replace(self, integration_id, resource_id, payload):
        pass

    @abstractmethod
    async def delete(self, integration_id, resource_id):
        pass


class FileResourceHandler(ResourceHandler):
    KEY="file"

    async def get(self, integration_id, resource_id=None):
        pass

    async def new(self, integration_id, payload):
        return await super().new(integration_id, payload)

    async def replace(self, integration_id, resource_id, payload):
        return await super().replace(integration_id, resource_id, payload)

    async def delete(self, integration_id, resource_id):
        return await super().delete(integration_id, resource_id)


class ExampleResourceHandler(ResourceHandler):
    KEY="example"

    async def get(self,  integration_id, resource_id=None):
        pass

    async def new(self, integration_id, payload):
        return await super().new(context_slug, integration_id, payload)

    async def replace(self,  integration_id, resource_id, payload):
        return await super().replace(context_slug, integration_id, resource_id, payload)

    async def delete(self, integration_id, resource_id):
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

    def stringify_serialization(self, obj):
        return json.loads(json.dumps(obj, default=str))

    async def call_in_context(
        self,
        session_id: str | None,
        target: str,
        function: str,
        args: typing.Optional[list] = None,
        kwargs: typing.Optional[dict] = None,
    ):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        retries = 0
        max_retries = 5
        interval = 3
        while True:
            try:
                session = await self.session_manager.get_session(name=session_id)
                break
            except Exception as err:
                logger.warning(f"Failed to get session, retrying: {retries}/{max_retries} {err}")
                await asyncio.sleep(interval)
                retries += 1
                if retries >= max_retries:
                    logger.error(f"Failed after {max_retries} retries. Giving up")
                    return None

        if session is not None:
            kernel = self.kernel_manager.get_kernel(session["kernel"]["id"])
        if not kernel:
            return None

        client = kernel.client()
        try:
            content = {
                "target": target,
                "function": function,
                "args": args,
                "kwargs": kwargs
            }
            msg = client.session.send(
                stream=client.shell_channel.socket,
                msg_or_type="call_in_context_request",
                content=content,
                track=True,
                metadata=None,
            )
            result = await client.get_shell_msg(timeout=5) # type: ignore
        finally:
            client.stop_channels()
        return result["content"]["return"]

# Integration Handler

class IntegrationHandler(BeakerAPIMixin, ExtensionHandlerMixin, JupyterHandler):
    """
    Handles fetching and adding integrations.
    """
    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

    async def head(self, session_id=None, integration_id=None):  # noqa: ARG002
        integrations = await self.call_in_context(
            session_id=session_id,
            target="context",
            function="list_integrations"
        ) or {}
        self.write({"integrations": list(integrations.keys())})

    async def get(self, session_id=None, integration_id=None):
        integrations = await self.call_in_context(
            session_id=session_id,
            target="context",
            function="list_integrations"
        ) or {}
        if integration_id is None:
            self.write({"integrations": self.stringify_serialization(integrations)})
        else:
            self.write(self.stringify_serialization(integrations.get(
                integration_id,
                {"error": "Integration does not exist on context."}
            )))

    async def post(self, session_id=None, integration_id=None):
        body = tornado.escape.json_decode(self.request.body)
        provider_id = body.pop("provider")
        if integration_id is not None:
            body["integration_id"] = integration_id
        try:
            result = await self.call_in_context(
                session_id=session_id,
                target=f"provider:{provider_id}",
                function="update_integration",
                kwargs=body
            )
            self.write({"status": "success", "result": result})
        except Exception as e:
            self.write({"status": "failure", "result": str(e)})


class IntegrationResourceHandler(BeakerAPIMixin, ExtensionHandlerMixin, JupyterHandler):
    """
    Handles fetching and adding resources belonging to an integration.
    """
    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

    async def head(self, session_id=None, integration_id=None, resource_type=None, resource_id=None):
        pass

    async def get(self, session_id=None, integration_id=None, resource_type=None, resource_id=None):
        # resource_cls = ResourceMap.get(resource_type, None)
        function = "list_resources" if resource_id is None else "get_resource"
        kwargs = {"integration_id": integration_id}
        # route disambiguation -- resource_type all means passing "none" to message, since it's required in route
        if resource_type is not None and resource_type != "all":
            kwargs["resource_type"] = resource_type
        if resource_id is not None:
            kwargs["resource_id"] = resource_id
        resources = await self.call_in_context(
            session_id=session_id,
            target=f"integration:{integration_id}",
            function=function,
            kwargs=kwargs
        )
        self.write({"resources": self.stringify_serialization(resources)})

    async def post(self, session_id=None, integration_id=None, resource_type=None, resource_id=None):
        function = "add_resource"
        kwargs = {"integration_id": integration_id}
        if resource_id is not None:
            function = "update_resource"
            kwargs["resource_id"] = resource_id
        kwargs |= tornado.escape.json_decode(self.request.body)
        try:
            result = await self.call_in_context(
                session_id=session_id,
                target=f"integration:{integration_id}",
                function=function,
                kwargs=kwargs
            )
            self.write({"status": "success", "details": result})
        except Exception as e:
            self.write({"status": "failure", "details": str(e)})


    async def delete(self, session_id=None, integration_id=None, resource_type=None, resource_id=None):
        try:
            await self.call_in_context(
                session_id=session_id,
                target=f"integration:{integration_id}",
                function="remove_resource",
                kwargs={"resource_id": resource_id, "integration_id": integration_id}
            )
            self.write({"status": "success", "details": ""})
        except Exception as e:
            self.write({"status": "failure", "details": str(e)})

handlers = [
    (r'integrations/(?P<session_id>[\w\d-]+)/?(?P<integration_id>[\w\d-]+)?', IntegrationHandler),
    (r'integrations/(?P<session_id>[\w\d-]+)/(?P<integration_id>[\w\d-]+)/(?P<resource_type>\w+)/?(?P<resource_id>[\w\d-]+)?', IntegrationResourceHandler),
]
