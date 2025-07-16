import os

from beaker_kernel.lib.config import config
from beaker_kernel.service.base import BaseBeakerServerApp
from beaker_kernel.service.auth.notebook import NotebookAuthorizer, NotebookIdentityProvider


def _jupyter_server_extension_points():
    return [{"module": "beaker_kernel.service.notebook", "app": BeakerNotebookApp}]


class BeakerNotebookApp(BaseBeakerServerApp):

    app_traits = {
        "authorizer_class": NotebookAuthorizer,
        "identity_provider_class": NotebookIdentityProvider,
    }

    def __init__(self, **kwargs):
        os.environ.setdefault("JUPYTER_TOKEN", config.jupyter_token)
        super().__init__(**kwargs)


if __name__ == "__main__":
    BeakerNotebookApp.launch_instance()
