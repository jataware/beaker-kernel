import os

from beaker_kernel.lib.config import config
from beaker_kernel.service.base import BaseBeakerServerApp, logger, BeakerKernelMappingManager, BeakerKernelManager
from beaker_kernel.service.auth import BeakerIdentityProvider, BeakerAuthorizer
from beaker_kernel.service.auth.notebook import NotebookAuthorizer, NotebookIdentityProvider

def _jupyter_server_extension_points():
    return [{"module": "beaker_kernel.service.server", "app": BeakerServerApp}]


class BeakerServerApp(BaseBeakerServerApp):
    log_requests = True
    app_traits = {
        "allow_root": True,
        "ip": "0.0.0.0",
        "authorizer_class": NotebookAuthorizer,
        "identity_provider_class": NotebookIdentityProvider,
    }

    def __init__(self, **kwargs):
        os.environ.setdefault("JUPYTER_TOKEN", config.jupyter_token)
        super().__init__(**kwargs)


if __name__ == "__main__":
    BeakerServerApp.launch_instance()
