import asyncio
import importlib
import json
import logging
import os
import traceback
import uuid
import urllib.parse
from typing import get_origin, get_args
from dataclasses import is_dataclass, asdict
from collections.abc import Mapping, Collection
from typing import get_origin, get_args, GenericAlias, Union, Generic, Generator, Optional, Any

from jupyter_server.auth.decorator import authorized
from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.extension.handler import ExtensionHandlerMixin
from jupyterlab_server import LabServerApp
from tornado import web, httputil
from tornado.web import StaticFileHandler, RedirectHandler, RequestHandler, HTTPError

from beaker_kernel.lib.autodiscovery import autodiscover
from beaker_kernel.lib.app import BeakerApp
from beaker_kernel.lib.context import BeakerContext
from beaker_kernel.lib.subkernel import BeakerSubkernel
from beaker_kernel.lib.agent_tasks import summarize
from beaker_kernel.lib.config import config, locate_config, Config, Table, Choice, recursiveOptionalUpdate, reset_config
from beaker_kernel.service import admin_utils

logger = logging.getLogger(__name__)

PREFIX = '/beaker/'


def add_handler_prefix(prefix: str, handler_tuple: tuple[str]):
    path, rest = handler_tuple[0], handler_tuple[1:]
    if not prefix.endswith('/'):
        prefix = prefix + '/'
    if path.startswith('/'):
        path = path.lstrip('/')

    return (urllib.parse.urljoin(prefix, path), *rest)


def register_api_handlers(app: LabServerApp):
    from .integrations import handlers as integration_handlers
    app.handlers.extend([
        add_handler_prefix(PREFIX, handler)
        for handler in integration_handlers
    ])
