import json
from typing import Any, Dict

from jinja2 import Template

# Persistent registry of templates, split into a tree structure by toolset, language, then name.
templates: Dict[str, Dict[str, Dict[str, Template]]] = {}

# Helper functions for retrieving/rendering the metadata and templates

def get_metadata(toolset: str, lang: str) -> Dict[str, Any]:
    metadata_json = get_template(toolset, lang, "metadata")
    return json.loads(metadata_json)


def get_template(toolset: str, lang: str, name: str, render_dict: Dict[str, Any]={}) -> str:
    template = templates[toolset][lang][name]
    return template.render(**render_dict)
