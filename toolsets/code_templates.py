import json
import os.path
from jinja2 import Environment, select_autoescape, FileSystemLoader, Template
from typing import Dict, Any

# Persistent registry of templates, split into a tree structure by toolset, language, then name.
templates: Dict[str, Dict[str, Dict[str, Template]]] = {}

# Locate templates and load in to the templates registry dictionary
jinja_env = Environment(
    loader=FileSystemLoader("toolsets/code_templates"),
    autoescape=select_autoescape()
)
for template_path in jinja_env.list_templates():
    template = jinja_env.get_template(template_path)
    dir_path, filename = os.path.split(template_path)
    toolset, lang = dir_path.split(os.path.sep)
    template_name, extension = os.path.splitext(filename)
    if toolset not in templates:
        templates[toolset] = {}
    if lang not in templates[toolset]:
        templates[toolset][lang] = {}
    templates[toolset][lang][template_name] = template


# Helper functions for retrieving/rendering the metadata and templates

def get_metadata(toolset: str, lang: str) -> Dict[str, Any]:
    metadata_json = get_template(toolset, lang, "metadata")
    return json.loads(metadata_json)


def get_template(toolset: str, lang: str, name: str, render_dict: Dict[str, Any]={}) -> str:
    template = templates[toolset][lang][name]
    return template.render(**render_dict)