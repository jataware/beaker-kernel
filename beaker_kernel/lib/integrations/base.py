import os
from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, Optional, Generator
from pathlib import Path

from ..types import Integration, Resource
from ..autodiscovery import find_resource_dirs

class BaseIntegrationProvider(ABC):

    provider_type: ClassVar[str]
    mutable: ClassVar[bool] = False
    slug: ClassVar[str]

    display_name: str
    prompt_instructions: Optional[str]

    def __init__(self, display_name: str):
        self.display_name = display_name
        self.prompt_instructions = None

    @classmethod
    def get_cls_data(cls) -> dict[str, os.PathLike]:
        return {}

    @property
    def prompt(self):
        integration_doc = self.__doc__ or ""
        parts = [
            f"Integration Name: {self.display_name}",
            "Integration description:",
            f"\t{integration_doc}",
        ]
        if self.prompt_instructions:
            parts.append(self.prompt_instructions)
        tools = self.tools
        if tools:
            parts.append("Provided tools:")
            for tool in tools:
                parts.append(f"\t{tool.name}")
        integrations = self.list_integrations()
        for integration in integrations:
            parts.append(str(integration))
        return "\n".join(parts)

    def iter_data(self, data_types: Optional[list[str] | str]=None) -> Generator[Path, None, None]:
        seen: set[tuple[str, str]] = set()
        if data_types is None:
            data_types = self.get_cls_data().keys()
        elif isinstance(data_types, str):
            data_types = [data_types]
        for data_path_base in self.data_basedirs:
            for data_type in data_types:
                type_path = Path(data_path_base) / data_type
                # Skip if generated path is not a directory
                if not type_path.is_dir():
                    continue
                for data_result in type_path.iterdir():
                    # Skip if seen a file of type and name already
                    key = (data_type, data_result.name)
                    if key in seen:
                        continue
                    seen.add(key)
                    yield data_result

    def get_file(self, data_type: str, name: os.PathLike) -> Optional[Path]:
        if os.path.isabs(name):
            raise IOError("Files retrieved by get_file cannot be absolute.")
        for data_dir in self.iter_data([data_type]):
            name_path = Path(name)
            # First check if file exists in path
            file_path = data_dir / name_path
            if file_path.exists():
                return file_path
            # If not, trim overlap of paths between the two paths.
            for i in range(len(data_dir.parts)):
                suffix = data_dir.parts[i:]  # possible overlap
                if name_path.parts[:len(suffix)] == suffix:
                    name_path = Path(*name_path.parts[len(suffix):])
                    break
            # Check if joined version with removed overlap exists.
            file_path = data_dir / name_path
            if file_path.exists():
                return file_path
        return None

    @property
    def data_basedirs(self):
        data_dirs = []
        for data_dir in find_resource_dirs("data"):
            base_dir = os.path.join(data_dir, self.slug)
            if os.path.isdir(base_dir):
                data_dirs.append(base_dir)
        alt_integration_dir = os.environ.get("INTEGRATION_PATH", "./integrations")
        if os.path.isdir(alt_integration_dir):
            data_dirs.append(alt_integration_dir)
        # Reverse dirs so we go from most specific to user to most general (global installs, etc)
        # This allows user to overwrite defaults
        data_dirs.reverse()
        return data_dirs

    @abstractmethod
    def list_integrations(self) -> list[Integration]:
        ...

    @abstractmethod
    def get_integration(self, integration_id: str) -> Integration:
        ...

    @abstractmethod
    def list_resources(self, integration_id: str, resource_type: Optional[str] = None) -> list[Resource]:
        ...

    @abstractmethod
    def get_resource(self, integration_id: str, resource_id: str) -> Resource:
        ...

    @property
    def tools(self) -> list[Callable]:
        tools = []
        for member_name in dir(self):
            # dir evaluates prompt due to @property
            if member_name == "tools" or member_name == "prompt":
                continue
            member = getattr(self, member_name)
            if callable(member) and getattr(member, '_is_tool', False):
                tools.append(member)
        return tools


class MutableBaseIntegrationProvider(BaseIntegrationProvider):
    mutable = True
    def __init__(self, display_name: str):
        super().__init__(display_name)

    @abstractmethod
    def add_integration(self, **payload) -> Integration:
        ...

    @abstractmethod
    def update_integration(self, integration_id: str, **payload) -> Integration:
        ...

    @abstractmethod
    def remove_integration(self, integration_id: str, **payload) -> None:
        ...

    @abstractmethod
    def add_resource(self, integration_id: str, **payload) -> Resource:
        ...

    @abstractmethod
    def update_resource(self, integration_id: str, resource_id: str, **payload) -> Resource:
        ...

    @abstractmethod
    def remove_resource(self, integration_id: str, resource_id: str, **payload) -> None:
        ...
