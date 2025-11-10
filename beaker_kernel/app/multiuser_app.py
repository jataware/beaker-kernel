from .server_app import BeakerServerApp

class BeakerMultiUserServerApp(BeakerServerApp):

    _default_app_traits = {
        "authorizer_class": "beaker_kernel.services.auth.dummy.DummyAuthorizer",
        "identity_provider_class": "beaker_kernel.services.auth.dummy.DummyIdentityProvider",
    }


if __name__ == "__main__":
    BeakerMultiUserServerApp.launch_instance()
