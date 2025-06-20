import inspect
from abc import ABC, abstractmethod




class BaseIntegrationProvider(ABC):

    @abstractmethod
    def list_integrations(self):
        ...

    @abstractmethod
    def get_integration(self, integration_id):
        ...

    @abstractmethod
    def add_integration(self, **payload):
        ...

    @abstractmethod
    def list_resources(self, integration_id, resource_type=None):
        ...

    @abstractmethod
    def get_resource(self, integration_id, resource_id):
        ...

    @abstractmethod
    def add_resource(self, integration_id, **payload):
        ...

    @property
    def tools(self) -> list[callable]:
        tools = inspect.getmembers(self, lambda member: callable(member) and getattr(member, '_is_tool', False))
        return tools
