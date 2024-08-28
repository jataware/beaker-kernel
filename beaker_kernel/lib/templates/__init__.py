from hatch.template import File
from hatch.utils.fs import Path
from typing import Any, ClassVar


class PathTemplate:
    def __init__(self, template: str, condition=None) -> None:
        self.template = template
        self.condition = condition

    def render(self, template_values) -> str:
        return self.template.format(**template_values)


class TemplateFile(File):
    PATH_PARTS: list[PathTemplate | str]
    TEMPLATE: str

    def __init__(self, path_parts: list[PathTemplate | str] | None = None, template: str | None = None):
        self.path_parts = path_parts or self.PATH_PARTS
        self.template = template or self.TEMPLATE

    def render_path(self, template_config: dict, plugin_config: dict):
        template_values = template_config.copy()
        template_values.update(plugin_config)

        parts = []
        for part in self.path_parts:
            if isinstance(part, PathTemplate):
                if part.condition and not part.condition(template_values):
                    continue
                parts.append(part.render(template_values))
            else:
                parts.append(str(part))
        return Path(*parts)

    def __call__(self, template_config: dict, plugin_config: dict) -> Any:
        template = self.template or self.TEMPLATE
        path = self.render_path(template_config, plugin_config)
        contents = template.format(**template_config)
        super().__init__(path, contents)
        return self


class InitFile(TemplateFile):
    TEMPLATE = ""  # Empty file

    def __init__(self, path_parts=None, template=None):
        super().__init__(path_parts=path_parts, template=template)
        if not self.path_parts[-1] == '__init__.py':
            self.path_parts.append('__init__.py')
