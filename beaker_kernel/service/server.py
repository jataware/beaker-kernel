import os

from beaker_kernel.service.base import BaseBeakerServerApp, logger


def _jupyter_server_extension_points():
    return [{"module": "beaker_kernel.service.server", "app": BeakerServerApp}]


class BeakerServerApp(BaseBeakerServerApp):
    log_requests = True
    app_traits = {
        "allow_root": True,
        "ip": "0.0.0.0",
    }


if __name__ == "__main__":
    BeakerServerApp.launch_instance()
