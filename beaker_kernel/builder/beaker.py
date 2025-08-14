import ast
import importlib
import importlib.util
import json
import os.path
import shutil
import sys
from collections import namedtuple
from typing import Any, TYPE_CHECKING
from hatchling.bridge.app import Application
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.metadata.core import ProjectMetadata
from hatchling.plugin import hookimpl
from pathlib import Path

if TYPE_CHECKING:
        from beaker_kernel.lib.app import BeakerApp
        from beaker_kernel.lib.integrations.base import BaseIntegrationProvider
        from beaker_kernel.lib.context import BeakerContext
        from beaker_kernel.lib.subkernel import BeakerSubkernel


ClassDef = namedtuple("ClassDef", ("mod_str", "class_name", "cls"))


class BuildError(Exception):
    pass


class BeakerBuildHook(BuildHookInterface):
    PLUGIN_NAME = "beaker"

    def __init__(self, root: str, config: dict[str, Any], build_config: Any, metadata: ProjectMetadata, directory: str, target_name: str, app: Application | None = None) -> None:
        super().__init__(root, config, build_config, metadata, directory, target_name, app)
        self.inserted_paths = set()

    def find_package_classes(self, packages):
        class_map = {}
        for package in packages:
            if package.startswith('src/'):
                package = str(Path(package).relative_to(Path('src/')))
            package: str = package.replace(os.path.sep, '.')
            base_mod = importlib.import_module(package)
            base_paths = map(Path, base_mod.__path__)

            # Walking the file tree ensures we are collecting the classes only from where they are actually defined and
            # not where they may happen to be imported. If we just inspected all of the modules, we would find the
            # classes, but wouldn't be able to differentiate imports from in-file definition.
            for base_path in base_paths:
                import_path = base_path.parent
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
                                relpath = fullpath.relative_to(import_path)
                                mod_str = str(relpath).removesuffix('.py').replace(os.path.sep, '.')
                                class_map[class_name] = (mod_str, str(import_path))
        return class_map

    def find_slugged_subclasses_of(self, subclass, packages=None) -> dict[str, ClassDef]:
        contexts = {}
        if packages is None:
            packages = self.build_config.packages

        class_map = self.find_package_classes(packages)

        # Actually import all of the modules, so we can inspect the classes to see if they are indeed the classes we
        # are looking for and, if so, extract any important information defined on them.
        for class_name, (mod_str, import_path) in class_map.items():
            mod = importlib.import_module(mod_str)
            cls = getattr(mod, class_name)
            if issubclass(cls, subclass) and cls is not subclass:
                slug = getattr(cls, 'SLUG', None) or getattr(cls, 'slug', None)
                if not slug:
                    continue
                contexts[slug] = ClassDef(mod_str, class_name, cls)
        return contexts

    def find_integration_data_files(self, integration_classes: "list[BaseIntegrationProvider]") -> dict[str, os.PathLike]:
        output = {}
        for integration_cls in integration_classes:
            # Fetch data mapping
            cls_data = integration_cls.get_cls_data()
            if not cls_data:
                continue
            for data_key, data_path in cls_data.items():
                base_path = Path(self.root)
                data_path = Path(data_path)
                abs_path = base_path.absolute() / data_path
                if not abs_path.exists():
                    raise IOError(
                        f"Integration data path '{abs_path}' does not exist.\n"
                        f"The 'data_path' value should be relative to the root directory which holds the pyproject.toml file and not the python source directory."
                    )
                if not abs_path.is_dir():
                    raise IOError(
                        f"Integration data path '{abs_path}' must point to a directory."
                    )
                output[os.path.join(integration_cls.slug, data_key)] = abs_path
        return output

    def add_packages_to_path(self, paths=None):
        if paths is None:
            paths = self.build_config.packages

        for package_path in paths:
            import_path = str(Path(package_path).absolute().parent)
            if import_path not in sys.path:
                sys.path.insert(0, import_path)
                self.inserted_paths.add(import_path)
        sys.path.insert(0, self.root)
        self.inserted_paths.add(self.root)

    def remove_packages_from_path(self):
        paths = getattr(self, "inserted_paths", set())
        for added_path in paths:
            sys.path.remove(added_path)


    def initialize(self, version, build_data):
        """Initialize the hook."""

        # Run for wheel building only
        if self.target_name != "wheel":
            return

        # If we are building beaker_kernel itself, we need to make sure the source is on the Python path so it can be
        # loaded.
        if any("beaker_kernel" in pkg for pkg in self.build_config.packages):
            local_path = os.path.abspath(os.curdir)
            sys.path.insert(0, local_path)
            self.inserted_paths.add(local_path)

        from beaker_kernel.lib.app import BeakerApp
        from beaker_kernel.lib.integrations.base import BaseIntegrationProvider
        from beaker_kernel.lib.context import BeakerContext
        from beaker_kernel.lib.subkernel import BeakerSubkernel

        dest = os.path.join(self.root, "build", "data_share_beaker")
        search_paths = self.build_config.packages or []

        self.add_packages_to_path()
        context_class_defs = self.find_slugged_subclasses_of(BeakerContext)
        subkernel_class_defs = self.find_slugged_subclasses_of(BeakerSubkernel)
        app_class_defs = self.find_slugged_subclasses_of(BeakerApp)
        integration_provider_class_defs = self.find_slugged_subclasses_of(BaseIntegrationProvider)
        integration_provider_classes = [class_def.cls for class_def in integration_provider_class_defs.values()]
        integration_data = self.find_integration_data_files(integration_provider_classes)
        self.remove_packages_from_path()

        if context_class_defs:
            print( "Found the following contexts:")
            for slug, class_def in context_class_defs.items():
                print(f"  '{slug}': {class_def.class_name} in package {class_def.mod_str}")
            print()
        if subkernel_class_defs:
            print( "Found the following subkernels:")
            for slug, class_def in subkernel_class_defs.items():
                print(f"  '{slug}': {class_def.class_name} in package {class_def.mod_str}")
            print()
        if app_class_defs:
            print("Found app: ")
            for slug, class_def in app_class_defs.items():
                print(f"  '{slug}': {class_def.class_name} in package {class_def.mod_str}")
        if integration_provider_class_defs:
            print("Found integration providers: ")
            for slug, class_def in integration_provider_class_defs.items():
                print(f"  '{slug}': {class_def.class_name} in package {class_def.mod_str}")
        if integration_data:
            print("Found integration data: ")
            for dest_path, data_path in integration_data.items():
                print(f"  '{dest_path}': {data_path}")

        # Recreate the destination directory, clearing any existing build artifacts
        if os.path.exists(dest):
           shutil.rmtree(dest)
        os.makedirs(dest)

        # Write out mappings for each context and subkernel to an individual json file
        for typename, src in [("contexts", context_class_defs), ("subkernels", subkernel_class_defs), ("apps", app_class_defs), ("integrations", integration_provider_class_defs)]:
            dest_dir = os.path.join(dest, typename)
            os.makedirs(dest_dir, exist_ok=True)
            # for slug, (package_name, class_name) in src.items():
            for slug, class_def in src.items():
                dest_file = os.path.join(dest_dir, f"{slug}.json")
                with open(dest_file, "w") as f:
                    json.dump({"slug": slug, "package": class_def.mod_str, "class_name": class_def.class_name}, f, indent=2)
                # Add shared-data mappings for each file so it is installed to the correct location
                self.build_config.shared_data[dest_file] = f"share/beaker/{typename}/{slug}.json"

        # Copy data files to proper location in build directory and update configuration
        for integration_data_path, integration_data_source in integration_data.items():
            integration_data_dest = os.path.join(dest, "data", integration_data_path)
            shutil.copytree(integration_data_source, integration_data_dest)
            self.build_config.shared_data[integration_data_dest] = f"share/beaker/data/{integration_data_path}"
