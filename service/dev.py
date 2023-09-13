import os

from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.extension.handler import (
    ExtensionHandlerJinjaMixin,
    ExtensionHandlerMixin,
)
from jupyter_server.utils import url_path_join as ujoin
from jupyterlab_server import LabServerApp

from main import AskemJupyterApp


HERE = os.path.join(os.path.dirname(__file__), "dev_ui")

def _jupyter_server_extension_points():
    return [{"module": __name__, "app": DevAskemJupyterApp}]

class DevHandler(ExtensionHandlerJinjaMixin, ExtensionHandlerMixin, JupyterHandler):
    """
    Serve a notebook file from the filesystem in the notebook interface
    """

    def get(self):
        """Get the main page for the application's interface."""
        # Options set here can be read with PageConfig.getOption
        mathjax_config = self.settings.get("mathjax_config", "TeX-AMS_HTML-full,Safe")
        mathjax_url = self.settings.get(
            "mathjax_url",
            "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js",
        )

        config_data = {
            # Use camelCase here, since that's what the lab components expect
            "baseUrl": self.base_url,
            "token": self.settings["token"],
            "notebookPath": "test.ipynb",
            "fullStaticUrl": ujoin(self.base_url, "static", self.name),
            "frontendUrl": ujoin(self.base_url, "example/"),
            "mathjaxUrl": mathjax_url,
            "mathjaxConfig": mathjax_config,
        }
        return self.write(
            self.render_template(
                "index.html",
                static=self.static_url,
                base_url=self.base_url,
                token=self.settings["token"],
                page_config=config_data,
            )
        )


class DevAskemJupyterApp(AskemJupyterApp):
    name = __name__
    load_other_extensions = True

    extension_url = "/dev_ui"
    default_url = "/dev_ui"
    app_url = "/dev_ui"
    app_settings_dir = os.path.join(HERE, "build", "application_settings")
    schemas_dir = os.path.join(HERE, "build", "schemas")
    static_dir = os.path.join(HERE, "build")
    templates_dir = os.path.join(HERE, "templates")
    themes_dir = os.path.join(HERE, "build", "themes")
    user_settings_dir = os.path.join(HERE, "build", "user_settings")
    workspaces_dir = os.path.join(HERE, "build", "workspaces")
    log_level = 10

    def initialize_handlers(self):
        super().initialize_handlers()
        """Add dev handler"""
        self.handlers.append(("/dev_ui", DevHandler))


if __name__ == "__main__":
    DevAskemJupyterApp.launch_instance()
