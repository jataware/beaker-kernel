from abc import ABC, abstractmethod
from typing import Callable, ClassVar


class BaseIntegrationProvider(ABC):
    display_name: str
    slug: str
    mutable: ClassVar[bool] = False

    def __init__(self, display_name: str):
        self.display_name = display_name
        self.slug = self.display_name.lower().replace(" ", "_")

    @abstractmethod
    def list_integrations(self):
        ...

    @abstractmethod
    def get_integration(self, integration_id):
        ...

    @abstractmethod
    def list_resources(self, integration_id, resource_type=None):
        ...

    @abstractmethod
    def get_resource(self, integration_id, resource_id):
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
