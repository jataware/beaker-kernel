import os

from beaker_kernel.service.base import BaseBeakerServerApp
# from beaker_kernel.service.auth.cognito import CognitoAuthorizer, CognitoHeadersIdentityProvider
from beaker_kernel.service.auth.dummy import DummyAuthorizer, DummyIdentityProvider
from traitlets import Bool


def _jupyter_server_extension_points():
    return [{"module": "beaker_kernel.service.multiuser", "app": BeakerMultiUserServerApp}]


class BeakerMultiUserServerApp(BaseBeakerServerApp):
    log_requests = Bool(True, help="Enable request logging", config=True)
    
    _default_app_traits = {
        "allow_root": True,
        "ip": "0.0.0.0",
        "authorizer_class": DummyAuthorizer,
        "identity_provider_class": DummyIdentityProvider,
    }


if __name__ == "__main__":
    print("multiuser")
    BeakerMultiUserServerApp.launch_instance()
