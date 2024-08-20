from pathlib import Path
from hatchling.plugin import hookimpl
from hatch.template.plugin.interface import TemplateInterface
from hatch.template import File
from hatch.template.files_default import PyProject

from beaker_kernel.lib.templates import InitFile
from beaker_kernel.lib.templates.paths import context_subdir, package_name
from beaker_kernel.lib.templates.agent_file import AgentFile
from beaker_kernel.lib.templates.context_file import ContextFile

class BeakerNewProjectTemplateHook(TemplateInterface):
    PLUGIN_NAME = 'beaker-new-project'
    PRIORITY = 200  # Run after 'default' which has priority 100

    def initialize_config(self, config):
        """
        Allow modification of the configuration passed to every file for new projects
        before the list of files are determined.
        """
        from importlib.metadata import version
        extra_dependencies = self.plugin_config.get("dependencies", [])

        config["dependencies"].add(f"beaker_kernel~={version('beaker_kernel')}")
        if extra_dependencies:
            config["dependencies"].update(extra_dependencies)

    def finalize_files(self, config, files):
        """Allow modification of files for new projects before they are written to the file system."""
        # Locate the PyProject file created by the 'default' plugin and add to the bottom of it before writing.
        file_map = {type(f): f for f in files}
        pyproject_file = file_map.get(PyProject, None)
        if pyproject_file:
            pyproject_file.contents += """
[tool.hatch.build.hooks.beaker]
require-runtime-dependencies = true
"""


class BeakerNewContextTemplateHook(TemplateInterface):
    PLUGIN_NAME = 'beaker-new-context'
    PRIORITY = 250  # Run after 'default' which has priority 100

    def initialize_config(self, config):
        """
        Allow modification of the configuration passed to every file for new projects
        before the list of files are determined.
        """
        class_base = self.plugin_config["class-base-name"]
        context_subdir = self.plugin_config.get("context-subdirectory", None)
        config["context_subdir"] = context_subdir
        config["context_name"] = self.plugin_config["context-name"]
        config["context_class"] = f"{class_base}Context"
        config["agent_class"] = f"{class_base}Agent"


    def get_files(self, config):
        """Add to the list of files for new projects that are written to the file system."""
        files = [
            ContextFile(),
            AgentFile(),
        ]
        if config["context_subdir"]:
            files.append(
                InitFile([package_name, context_subdir, '__init__.py'])
            )
        return files
