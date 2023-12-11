import importlib
import importlib.util
import json
import logging
import os
import sys
from typing import Dict


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


def autodiscover(type) -> Dict[str, type]:
    """
    Auto discovers installed
    """
    items = {}
    for location in LIB_LOCATIONS:
        mapping_dir = os.path.join(location, type)
        if os.path.exists(mapping_dir):
            for mapping in os.listdir(mapping_dir):
                fullpath = os.path.join(mapping_dir, mapping)
                try:
                    with open(fullpath) as mapping_file:
                        data = json.load(mapping_file)
                    slug = data["slug"]
                    package = data["package"]
                    class_name = data["class_name"]
                except (json.JSONDecodeError, KeyError) as err:
                    logger.error(f"Unable to parse the {type} file '{fullpath}", exc_info=err)
                    continue
                module = importlib.import_module(package)
                discovered_class = getattr(module, class_name)
                items[slug] = discovered_class
    return items
