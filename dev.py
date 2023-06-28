import os

from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.extension.handler import ExtensionHandlerJinjaMixin, ExtensionHandlerMixin
from jupyter_server.utils import url_path_join as ujoin
from jupyterlab_server import LabServerApp



HERE = os.path.join(os.path.dirname(__file__), "dev_ui")


version = "0.0.1"

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
            "mathjax_url", "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js"
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



class DevAskemJupyterApp(LabServerApp):
    name = __name__
    # load_other_extensions = False
    app_name = "Askem Jupyter App"
    app_version = version
    allow_origin = "*"

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


    def initialize_handlers(self):
        """Bypass initializing the default handler since we don't need to use the webserver, just the websockets."""
        self.handlers.append(("/dev_ui", DevHandler))


    def initialize_settings(self):
        # Override to allow cross domain websockets
        self.settings['allow_origin'] = '*'
        self.settings['disable_check_xsrf'] = True


if __name__ == "__main__":
    DevAskemJupyterApp.launch_instance()


