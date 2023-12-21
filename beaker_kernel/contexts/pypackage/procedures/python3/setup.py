import importlib
import inspect
import os
import pydoc
import sys


def _walk_package(package_name: str):
    """
    Take a package or module string and returns all importable modules/subpackages.
    """
    if '.' in package_name:
        package_name = package_name.split('.', 1)[0]
    pkg = importlib.import_module(package_name)
    pkgpath = pkg.__file__
    if pkgpath.endswith("__init__.py"):
        pkgpath = os.path.dirname(pkgpath)
    else:
        yield (package_name, pkgpath)
    for dirpath, dirnames, filenames in os.walk(pkgpath, topdown=True):
        if "__init__.py" not in filenames:
            continue
        for filename in sorted(filenames, key=lambda fname: (not fname.startswith('__'), fname)):
            if filename.endswith(".py"):
                base_module_import_str = dirpath.replace(pkgpath, pkg.__name__).replace(os.path.sep, '.')
                if filename == '__init__.py':
                    dot_syntax = base_module_import_str
                else:
                    dot_syntax = f"{base_module_import_str}.{filename[:-3]}"
                yield (dot_syntax, os.path.join(dirpath, filename))


def _get_map(package_name):
    """
    Gets the full map of modules, classes, functions and data objects in a library/package.
    """

    output = []
    for module_str, module_file in _walk_package(package_name):
        try:
            mod = importlib.import_module(module_str)
        except ImportError as err:
            continue
        except Exception as err:
            print(f"Couldn't import {module_str}, {module_file} due to error {err}")
        synopsis, _ = pydoc.splitdoc(pydoc.getdoc(mod))
        all = getattr(mod, '__all__', None)
        if all:
            members = [(member_name, getattr(mod, member_name)) for member_name in all]
        else:
            members = inspect.getmembers(mod)

        classes = []
        functions = []
        data = []
        for member_name, member in members:
            # Skip private members and members that don't belong to this module (i.e. is imported from elsewhere)
            if member_name.startswith("_") or inspect.getmodule(member) is not mod or member_name in ('tests', 'test', 'testing'):
                continue
            member_synopsis, _ = pydoc.splitdoc(pydoc.getdoc(member))
            if inspect.isclass(member):
                member_synopsis, _ = pydoc.splitdoc(pydoc.getdoc(member))
                classes.append((member_name, member_synopsis))
            elif inspect.isroutine(member):
                member_synopsis, _ = pydoc.splitdoc(pydoc.getdoc(member))
                functions.append((member_name, member_synopsis))
            else:
                data.append((member_name, member_synopsis))

        if classes or functions or data:
            output.append(f"Module: `{module_str}` ({module_file}){' *' if mod in globals().values() else ''}")
            if synopsis:
                output.append(f"  {synopsis}")
            output.append("")

            if classes:
                output.append("  Classes:")
                for cls_name, synopsis in classes:
                    output.append(f"    {cls_name}")
                    if synopsis:
                        output.append(f"      {synopsis}")
                    output.append("")
            if functions:
                output.append("  Functions:")
                for func_name, synopsis in functions:
                    output.append(f"    {func_name}")
                    if synopsis:
                        output.append(f"      {synopsis}")
                    output.append("")
            if data:
                output.append("  Data:")
                for data_name, synopsis in data:
                    output.append(f"    {data_name}")
                    if synopsis:
                        output.append(f"      {synopsis}")
                    output.append("")
        output.append("")

    return "\n".join(output)
