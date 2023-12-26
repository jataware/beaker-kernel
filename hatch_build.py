"""Custom hatch build hook"""
import ast
import importlib
import inspect
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomHook(BuildHookInterface):
    """The IPykernel build hook."""

    def initialize(self, version, build_data):
        """Initialize the hook."""

        here = os.path.dirname(__file__)
        dest = os.path.join("build", "data_share_beaker")

        # Import code into build environment
        sys.path.insert(0, str(here))

        # Recreate the destination directory, clearing any existing build artifacts
        if os.path.exists(dest):
           shutil.rmtree(dest)
        os.makedirs(dest)

        # Inspect context files to build a dynamic mapping of context slugs to context classes
        context_classes = {}
        context_src = os.path.join(here, "beaker_kernel", "contexts")
        if os.path.exists(context_src):
            for fpath in os.listdir(context_src):
                if fpath.startswith("_"):
                    continue
                package_name = f"beaker_kernel.contexts.{fpath}.context"
                slug = fpath
                full_path = os.path.join(context_src, fpath, "context.py")
                with open(full_path) as f:
                    src = f.read()
                symbols = ast.parse(src, full_path)
                for symbol in symbols.body:
                    if isinstance(symbol, ast.ClassDef) and "BaseContext" in [attr.id for attr in getattr(symbol, "bases", [])]:
                        if slug in context_classes:
                            raise SyntaxError("Only one context is allowed to be defined per module.")
                        class_name = symbol.name
                        context_classes[slug] = (package_name, class_name)


        # Inspect subkernel files to build a dynamic map of defined subkernels
        subkernel_classes = {}
        subkernel_src = os.path.join(here, "beaker_kernel", "lib", "subkernels")
        if os.path.exists(subkernel_src):
            for fpath in os.listdir(subkernel_src):
                if fpath.startswith("_") or fpath.startswith("base"):
                    continue
                package_name = f"beaker_kernel.lib.subkernels.{os.path.splitext(fpath)[0]}"
                module = importlib.import_module(package_name)
                subkernel_list = inspect.getmembers(module, lambda member: inspect.isclass(member) and not member.__name__.startswith("Base"))
                for class_name, class_instance in subkernel_list:
                    slug = getattr(class_instance, "SLUG")
                    if slug in context_classes:
                        raise SyntaxError("Only one context is allowed to be defined per module.")
                    subkernel_classes[slug] = (package_name, class_name)


        build_config = self.build_config.build_config
        shared_data = build_config["targets"]["wheel"]["shared-data"]

        # Map the main beaker kernel for inclusion/installation
        kernel_json_file = os.path.join(here, "beaker_kernel", "kernel.json")
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
