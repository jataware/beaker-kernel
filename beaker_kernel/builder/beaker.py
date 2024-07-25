import ast
import importlib
import importlib.util
import json
import os.path
import shutil
import sys
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.plugin import hookimpl
from pathlib import Path

from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.subkernels.base import BaseSubkernel


class BuildError(Exception):
    pass


class BeakerBuildHook(BuildHookInterface):
    PLUGIN_NAME = "beaker"

    def find_package_classes(self, packages):
        class_map = {}
        for package in packages:
            base_mod = importlib.import_module(package)
            base_paths = base_mod.__path__

            # Walking the file tree ensures we are collecting the classes only from where they are actually defined and
            # not where they may happen to be imported. If we just inspected all of the modules, we would find the
            # classes, but wouldn't be able to differentiate imports from in-file definition.
            for base_path in base_paths:
                for dirpath, _, filenames in os.walk(base_path):
                    path = Path(dirpath)
                    if path.name.startswith("_"):
                        continue
                    if '__init__.py' not in filenames:
                        continue
                    for filename in filenames:
                        if not filename.endswith('.py'):
                            continue
                        fullpath = path / filename
                        with open(fullpath) as f:
                            src = f.read()
                        symbols = ast.parse(src, fullpath)
                        for symbol in symbols.body:
                            if isinstance(symbol, ast.ClassDef):
                                class_name = symbol.name
                                relpath = Path(fullpath).relative_to(Path(base_path).parent)
                                mod_str = str(relpath).removesuffix('.py').replace('/', '.')
                                class_map[class_name] = mod_str
        return class_map

    def find_slugged_subclasses_of(self, subclass, packages=None):
        contexts = {}
        if packages is None:
            packages = self.build_config.packages

        class_map = self.find_package_classes(packages)

        # Actually import all of the modules, so we can inspect the classes to see if they are indeed the classes we
        # are looking for and, if so, extract any important information defined on them.
        for class_name, mod_str in class_map.items():
            try:
                mod = importlib.import_module(mod_str)
            except ModuleNotFoundError as err:
                sys.stderr.write(f"Warning: Module {mod_str} not found. There may be an issue with your "
                                    "configuration.\n")
                sys.stderr.flush()
                continue
            cls = getattr(mod, class_name)
            if issubclass(cls, subclass) and cls is not subclass:
                slug = getattr(cls, 'SLUG', None)
                if not slug:
                    continue
                contexts[slug] = (mod_str, class_name)
        return contexts


    def initialize(self, version, build_data):
        """Initialize the hook."""

        # Run for wheel building only
        if self.target_name != "wheel":
            return

        # Ensure needed structure is intact
        build_config = self.build_config.build_config
        if "targets" not in build_config:
            build_config["targets"] = {}
        if "wheel" not in build_config["targets"]:
            build_config["targets"]["wheel"] = {}

        dest = os.path.join(self.root, "build", "data_share_beaker")
        search_paths = self.build_config.packages or []

        context_paths = self.config.get("context_paths", [])
        subkernel_paths = self.config.get("subkernel_paths", [])

        context_base_paths = self.config.get("context_base_paths", search_paths)
        subkernel_base_paths = self.config.get("subkernel_base_paths", search_paths)

        contexts = self.config.get("contexts", [])
        subkernels = self.config.get("subkernels", [])

        # if not context_paths or True:
        #     context_paths = self.find_contexts_in_packages(self.build_config.packages)
        #     print("contexts:")
        #     pprint.pprint(context_paths)

        context_classes = self.find_slugged_subclasses_of(BaseContext)
        subkernel_classes = self.find_slugged_subclasses_of(BaseSubkernel)

        # Recreate the destination directory, clearing any existing build artifacts
        if os.path.exists(dest):
           shutil.rmtree(dest)
        os.makedirs(dest)

        if "shared-data" in build_config["targets"]["wheel"]:
            shared_data = build_config["targets"]["wheel"]["shared-data"]
        else:
            shared_data = {}
            build_config["targets"]["wheel"]["shared-data"] = shared_data

        # Map the main beaker kernel for inclusion/installation
        kernel_json_file = os.path.join(self.root, "beaker_kernel", "kernel.json")
        shared_data[kernel_json_file] = f"share/jupyter/kernels/beaker_kernel/kernel.json"

        # Write out mappings for each context and subkernel to an individual json file
        for typename, src in [("contexts", context_classes), ("subkernels", subkernel_classes)]:
            dest_dir = os.path.join(dest, typename)
            os.makedirs(dest_dir, exist_ok=True)
            for slug, (package_name, class_name) in src.items():
                dest_file = os.path.join(dest_dir, f"{slug}.json")
                with open(dest_file, "w") as f:
                    json.dump({"slug": slug, "package": package_name, "class_name": class_name}, f, indent=2)
                # Add wheel.shared-data mappings for each file so it is installed to the correct location
                shared_data[dest_file] = f"share/beaker/{typename}/{slug}.json"


@hookimpl
def hatch_register_build_hook():
    return BeakerBuildHook