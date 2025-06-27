from beaker_kernel.service.base import BaseBeakerServerApp


def _jupyter_server_extension_points():
    return [{"module": "beaker_kernel.service.notebook", "app": BeakerNotebookApp}]


class BeakerNotebookApp(BaseBeakerServerApp):
    pass


if __name__ == "__main__":
    BeakerNotebookApp.launch_instance()
