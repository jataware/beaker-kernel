import importlib
import importlib.util
import json
import logging
import os
import sys
import typing
from collections.abc import Mapping
# from typing import Dict


logger = logging.getLogger(__name__)

# Sorted from more general to more specific. Items discovered lower/more specific locations will override
# more general items with the same slug.
if sys.platform == "win32":
    LIB_LOCATIONS = [
        r'%PROGRAMDATA\beaker',
        r'%APPDATA%\beaker',
        r'%LOCALAPPDATA%\beaker',
        os.path.join(sys.prefix, "share", "beaker"),
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


MappingType = typing.Literal["contexts", "subkernels", "apps", "commands"]

def find_mappings(mapping_type: MappingType) -> typing.Generator[typing.Dict[str, any], None, None]:
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


class AutodiscoveryItems(Mapping[str, type|dict[str, str]]):
    raw: dict[str, type|dict[str, str]]
    mapping: dict[str, type|dict]

    def __init__(self, *args, **kwargs):
        self.mapping = {}
        self.raw = dict(*args, **kwargs)

    def __getitem__(self, key):
        item = self.mapping.get(key, self.raw.get(key))
        if isinstance(item, (str, bytes, os.PathLike)) and os.path(path := os.fspath(item)) and path.endswith('.json'):
            with open(path) as jsonfile:
                item = json.load(jsonfile)
                item["mapping_file"] = path
        match item:
            case type():
                return item
            case {"slug": slug, "package": package, "class_name": class_name, **kw}:
                mapping_file = kw.get("mapping_file", None)
                try:
                    module = importlib.import_module(package)
                except (ImportError, ModuleNotFoundError) as err:
                    # logger.warning(f"Warning: Beaker module '{package}' in file {mapping_file} is unable to be imported. See below.")
                    # logger.warning(f"  {err.__class__}: {err.msg}")
                    raise
                assert slug == key
                discovered_class = getattr(module, class_name)
                if mapping_file:
                    setattr(discovered_class, '_autodiscovery', {
                        "mapping_file": mapping_file,
                        **item
                    })
                self.mapping[key] = discovered_class
                return discovered_class
            case _:
                raise ValueError(f"Unable to handle autodiscovery item '{item}' (type '{item.__class__}')")

    def __setitem__(self, key, value):
        self.raw[key] = value

    def __iter__(self):
        yield from self.raw.__iter__()

    def __len__(self):
        return len(self.raw)


def autodiscover(mapping_type: MappingType) -> typing.Dict[str, type]:
    """
    Auto discovers installed classes of specified types.
    """
    items: AutodiscoveryItems = AutodiscoveryItems()
    for mapping_file, data in find_mappings(mapping_type):
        slug = data["slug"]
        items[slug] = {"mapping_file": mapping_file, **data}
    return items
