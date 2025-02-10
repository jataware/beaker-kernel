from dataclasses import dataclass, field, asdict
from collections import deque
from collections.abc import Mapping
import importlib.metadata
import os
import importlib
import json
import string
import typing
from typing import TypedDict, Optional, ClassVar, Sequence, Iterable, Iterator


class TemplateFormatter(string.Formatter):
    """Custom formatter to allow formats that match "{type}:{slug}():{attr})?"."""
    CUSTOM_TYPES = ["asset",]

    def parse(self, format_string):
        for literal_text, field_name, format_spec, conversion in super().parse(format_string):
            if field_name in self.CUSTOM_TYPES:
                yield literal_text, f"{field_name}:{format_spec}", "", None
            else:
                yield literal_text, field_name, format_spec, conversion

    def get_value(self, key, args, kwargs):
        try:
            return super().get_value(key, args, kwargs)
        except KeyError:
            return ""
formatter = TemplateFormatter()

class TemplateString(str):
    _refs: set[str]

    def __init__(self, value):
        super().__init__()
        self._refs = set(
            var_name for _, var_name, _, _ in formatter.parse(self) if var_name
        )

    def render(self, bundle: "TemplateStringBundle"):
        return formatter.format(self, **bundle.render())


class TemplateStringBundle(Mapping[str, TemplateString]):
    app_name: TemplateString
    short_title: TemplateString
    chat_welcome_html: TemplateString

    _mapping: dict[str, TemplateString]
    _render_cache: list
    _rendering: bool

    def __init__(self, assets=None, **templates:Mapping[str, str|TemplateString]):
        self._mapping = {}
        self._render_cache = None
        self._rendering = False
        for template_slug, template_string in templates.items():
            self[template_slug] = template_string
        if assets:
            self.set_assets(assets)

    def set_assets(self, assets: "list[BeakerAppAsset]"):
        for asset in assets:
            self[f"asset:{asset.slug}:src"] = TemplateString(asset.src)
            for attr_name, attr_value in asset.attrs.items():
                self[f"asset:{asset.slug}:{attr_name}"] = TemplateString(attr_value)

    def __getitem__(self, key: str) -> TemplateString:
        return self._mapping[key]

    def __setitem__(self, key, value):
        self._render_cache = None
        if not isinstance(value, TemplateString):
            value = TemplateString(value)
        self._mapping[key] = value

    def __iter__(self):
        return self._mapping.__iter__()

    def __len__(self):
        return self._mapping.__len__()

    @property
    def rendered(self) -> bool:
        return bool(self._render_cache)

    def sort_for_render(self) -> list[tuple[str, TemplateString]]:
        # Build the graph and in-degree count
        graph = {key: [] for key in self}
        in_degree = {key: 0 for key in self}

        # Populate the graph with edges based on dependencies
        for key, item in self.items():
            for ref in item._refs:
                if ref not in self:
                    raise ValueError(f"Dependency '{ref}' for item '{key}' not found in items.")
                graph[ref].append(key)
                in_degree[key] += 1

        # Initialize the queue with items having zero in-degree (no dependencies)
        queue = deque([key for key, degree in in_degree.items() if degree == 0])
        sorted_items = []

        # Process items in topological order
        while queue:
            current = queue.popleft()
            sorted_items.append(current)

            # Decrease in-degree of dependent items
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles in the dependency graph
        if len(sorted_items) != len(self):
            raise ValueError("Cycle detected in dependencies.")

        return [(key, self[key]) for key in sorted_items]

    def render(self) -> dict[str, str]:
        try:
            self._rendering = True
            result = {}
            if self.rendered:
                return self._render_cache
            else:
                for key, value in self.sort_for_render():
                    result[key] = formatter.format(value, **result)
                self._render_cache = result
                return result
        finally:
            self._rendering = False


@dataclass
class BeakerAppAsset:
    slug: str
    src: str
    attrs: dict[str, str]

    def __init__(self, slug, src, **attrs):
        self.slug = slug
        self.src = src
        self.attrs = attrs

    def asdict(self):
        return asdict(self)


@dataclass
class Context:
    slug: str
    payload: dict[str, any] = field(default_factory=lambda: {})
    single_context: bool = False

    def asdict(self):
        return asdict(self)


@dataclass
class Page:
    slug: str
    title: Optional[str|TemplateString] = None
    default: Optional[bool] = False
    stylesheet: Optional[str] = None  # field(default_factory=lambda: {})

    def __post_init__(self):
        if self.title is None:
            self.title = TemplateString(f"{{app_name}} {self.slug.capitalize()}")
        if isinstance(self.stylesheet, str):
            self.stylesheet = TemplateString(self.stylesheet)

    def asdict(self, app: "BeakerApp"):
        title = TemplateString(self.title).render(app.template_bundle)
        if isinstance(self.stylesheet, TemplateString):
            stylesheet = self.stylesheet.render(app.template_bundle)
        else:
            stylesheet = self.stylesheet
        return {
            "slug": self.slug,
            "title": title,
            "default": self.default,
            "stylesheet": stylesheet,
        }


class BeakerApp:
    """
    """

    # Configuration settings
    slug: ClassVar[str]
    name: ClassVar[Optional[str]] = None
    default_title: ClassVar[Optional[str]] = None
    asset_dir: ClassVar[Optional[os.PathLike]] = None
    default_context: ClassVar[Optional[Context]] = None
    template_bundle: ClassVar[Optional[TemplateStringBundle]] = None
    template_bundle_cls: ClassVar[Optional[type[TemplateStringBundle]]] = None
    pages: ClassVar[dict[str, Page]] = {}
    stylesheet: ClassVar[Optional[str]] = None
    assets: ClassVar[list[BeakerAppAsset]] = []

    # Internal
    _assets: list[BeakerAppAsset]
    _template_bundle: TemplateStringBundle
    _default_title: str
    _pages: dict[str, Page]

    def __init_subclass__(cls):
        if not cls.slug:
            raise ValueError("ClassVar 'slug' is required.")

    def __init__(self):
        self._assets = [
            BeakerAppAsset(
                slug=asset.slug,
                src=os.path.join("/assets", self.slug, asset.src),
                **asset.attrs
            ) for asset in self.__class__.assets
        ]

        if self.template_bundle == TemplateStringBundle:
            # A class was passed in, initialize it?
            # TODO: Think about logic here. Should error?
            self._template_bundle = self.template_bundle()
        else:
            self._template_bundle = self.template_bundle
        self._template_bundle["app_slug"] = TemplateString(self.slug)
        self._template_bundle.set_assets(self._assets)

        if self.name is None:
            try:
                package_metadata = importlib.metadata.metadata(__package__)
                name = package_metadata["Name"]
            except importlib.metadata.PackageNotFoundError:
                name = None
            if not name:
                name = self.slug
            self.name = name.capitalize().replace("_", " ")
        self._template_bundle["app_name"] = TemplateString(self.name)

        self._pages = {
            slug: (page if isinstance(page, Page) else Page(slug=slug, **page)) for slug, page in self.pages.items()
        }
        self._default_title = TemplateString(self.default_title) if self.default_title else self.name


    def get_stylesheet(self) -> dict[str, str] | str:
        if self.stylesheet:
            if isinstance(self.stylesheet, str):
                return TemplateString(self.stylesheet).render(self.template_bundle)
            elif isinstance(self.stylesheet, TemplateString):
                return self.stylesheet.render(self.template_bundle)
            else:
                return self.stylesheet


    def get_title(self, page_slug: Optional[str]=None) -> str|None:
        title = None
        if page_slug:
            if page_slug in self.pages:
                title = self.pages[page_slug].title
            else:
                if self._default_title:
                    title =  f"{self._default_title} {page_slug.capitalize()}"
                else:
                    title = r"{app_name}"
        else:
            title = self._default_title
        return TemplateString(title).render(self.template_bundle)


    @property
    def templates(self) -> dict[str, str]:
        return self._template_bundle.render()

    def to_javascript(self, page=None) -> str:
        output = [
            r"window.beaker_app = {};"
        ]

        page_title = self.get_title(page)
        if page_title:
            output.append(
                rf"""document.title = {json.dumps(page_title)};"""
            )

        if self.pages:
            output.append(
                rf"""window.beaker_app.pages = {json.dumps({page_slug: page.asdict(app=self) for page_slug, page in self._pages.items()})};"""
            )
        if self._template_bundle:
            output.append(
                rf"""window.beaker_app.templateStrings = {json.dumps(self.templates)};"""
            )
        if self.default_context:
            output.append(
                rf"""window.beaker_app.default_context = {json.dumps(self.default_context.asdict())};"""
            )
        if self._assets:
            output.append(
                rf"""window.beaker_app.assets = {json.dumps({asset.slug: asset.asdict() for asset in self._assets})};"""
            )
        if self.stylesheet:
            output.append(
                rf"""window.beaker_app.stylesheet = {json.dumps(self.get_stylesheet())}"""
            )
#         for idx, stylesheet in enumerate(self.get_stylesheets()):
#             output.append(
#                 rf"""\
# let style{idx} = document.createElement("style");
# style{idx}.type = "text/css";
# style{idx}.textContents = `{stylesheet}`;
# document.head.appendChild(style{idx});
# """
#             )
        return "\n".join(output)
