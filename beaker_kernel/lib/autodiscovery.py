import importlib
import importlib.util
import json
import logging
import os
import sys
import typing
# from typing import Dict


logger = logging.getLogger(__name__)

# Sorted from more general to more specific. Items discovered lower/more specific locations will override
# more general items with the same slug.
if sys.platform == "win32":
    LIB_LOCATIONS = [
        r'%PROGRAMDATA\beaker',
        r'%APPDATA%\beaker',
        r'%LOCALAPPDATA%\beaker',
    ]
elif sys.platform == "darwin":
    LIB_LOCATIONS = [
        "/usr/share/beaker",
        "/usr/local/share/beaker",
        os.path.join(sys.prefix, "share", "beaker"),
        os.path.expanduser("~/.local/share/beaker"),
        os.path.expanduser("~/Library/Beaker"),
    ]
else:
    LIB_LOCATIONS = [
        "/usr/share/beaker",
        "/usr/local/share/beaker",
        os.path.join(sys.prefix, "share", "beaker"),
        os.path.expanduser("~/.local/share/beaker"),
    ]
    if "XDG_DATA_HOME" in os.environ:
        LIB_LOCATIONS.append(os.path.join(os.environ["XDG_DATA_HOME"], "beaker"))


MappingType = typing.Literal["context", "subkernel"]

def find_mappings(mapping_type: MappingType) -> typing.Dict[str, any]:
    """
    Finds, reads, and parses all mappings of the provided type.
    """
    for location in LIB_LOCATIONS:
        mapping_dir = os.path.join(location, mapping_type)
        if os.path.exists(mapping_dir):
            for mapping in os.listdir(mapping_dir):
                fullpath = os.path.join(mapping_dir, mapping)
                try:
                    with open(fullpath) as mapping_file:
                        data = json.load(mapping_file)
                        yield fullpath, data
                except (json.JSONDecodeError, KeyError) as err:
                    logger.error(f"Unable to parse the {mapping_type} file '{fullpath}", exc_info=err)
                    continue


def autodiscover(mapping_type: MappingType) -> typing.Dict[str, type]:
    """
    Auto discovers installed
    """
    items = {}
    for mapping_file, data in find_mappings(mapping_type):
        slug = data["slug"]
        package = data["package"]
        class_name = data["class_name"]
        try:
            module = importlib.import_module(package)
        except (ImportError, ModuleNotFoundError) as err:
            logger.warning(f"Warning: Beaker module '{package}' in file {mapping_file} is unable to be imported. See below.")
            logger.warning(f"  {err.__class__}: {err.msg}")
            continue
        discovered_class = getattr(module, class_name)
        setattr(discovered_class, '_autodiscovery', {
            "mapping_file": mapping_file,
            **data
        })

        items[slug] = discovered_class
    return items
