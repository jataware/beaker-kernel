from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, Optional

from ..types import Integration, Resource

class BaseIntegrationProvider(ABC):

    provider_type: ClassVar[str]
    mutable: ClassVar[bool] = False

    display_name: str
    slug: str
    prompt_instructions: Optional[str]

    def __init__(self, display_name: str):
        self.display_name = display_name
        self.slug = self.display_name.lower().replace(" ", "_")
        self.prompt_instructions = None

    @property
    def prompt(self):
        integration_doc = self.__doc__ or "Foo"
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
            if member_name == "tools":
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
    def add_integration(self, **payload):
        ...

    @abstractmethod
    def update_integration(self, **payload):
        ...

    @abstractmethod
    def remove_integration(self, **payload):
        ...

    @abstractmethod
    def add_resource(self, integration_id, **payload):
        ...

    @abstractmethod
    def update_resource(self, integration_id, resource_id, **payload):
        ...

    @abstractmethod
    def remove_resource(self, integration_id, resource_id, **payload):
        ...
