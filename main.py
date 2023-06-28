import os

from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.extension.handler import ExtensionHandlerJinjaMixin, ExtensionHandlerMixin
from jupyter_server.utils import url_path_join as ujoin
from jupyterlab_server import LabServerApp


HERE = os.path.dirname(__file__)

version = "0.0.1"

def _jupyter_server_extension_points():
    return [{"module": __name__, "app": AskemJupyterApp}]


class AskemJupyterApp(LabServerApp):

    name = __name__
    load_other_extensions = False
    app_name = "Askem Jupyter App"
    app_version = version
    allow_origin = "*"

    def initialize_handlers(self):
        """Bypass initializing the default handler since we don't need to use the webserver, just the websockets."""
        pass
        

    def initialize_settings(self):
        # Override to allow cross domain websockets
        self.settings['allow_origin'] = '*'
        self.settings['disable_check_xsrf'] = True

if __name__ == "__main__":
    AskemJupyterApp.launch_instance()


