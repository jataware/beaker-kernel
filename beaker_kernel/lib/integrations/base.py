import inspect
from abc import ABC, abstractmethod


class BaseIntegrationProvider(ABC):
    display_name: str
    mutable: bool
    def __init__(self, display_name: str):
        self.mutable = False
        self.display_name = display_name

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
    def tools(self) -> list[callable]:
        tools = []
        for member_name in dir(self):
            if member_name == "tools":
                continue
            member = getattr(self, member_name)
            if callable(member) and getattr(member, '_is_tool', False):
                tools.append(member)
        return tools


class MutableBaseIntegrationProvider(BaseIntegrationProvider):
    def __init__(self, display_name: str):
        super().__init__(display_name)
        self.mutable = True

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
