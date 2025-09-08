import os

from beaker_kernel.lib.config import config
from beaker_kernel.service.base import BaseBeakerServerApp, logger, BeakerKernelMappingManager, BeakerKernelManager
from beaker_kernel.service.auth import BeakerIdentityProvider, BeakerAuthorizer
from beaker_kernel.service.auth.notebook import NotebookAuthorizer, NotebookIdentityProvider
from traitlets import Bool

# from .provisioning import DockerProvisioner

def _jupyter_server_extension_points():
    return [{"module": "beaker_kernel.service.server", "app": BeakerServerApp}]


class BeakerServerApp(BaseBeakerServerApp):
    log_requests = Bool(True, help="Enable request logging", config=True)

    _default_app_traits = {
        "allow_root": True,
        "ip": "0.0.0.0",
        "authorizer_class": NotebookAuthorizer,
        "identity_provider_class": NotebookIdentityProvider,
    }

    def __init__(self, **kwargs):
        """Initialize BeakerServerApp for hosted server use.

        Sets up the Jupyter token from configuration and initializes
        the server with logging enabled.
        """
        os.environ.setdefault("JUPYTER_TOKEN", config.jupyter_token)
        super().__init__(**kwargs)
    # provisioner_class = DockerProvisioner
    # provisioner_options = {}


if __name__ == "__main__":
    BeakerServerApp.launch_instance()
