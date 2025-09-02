import typing
from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import uuid4
from beaker_kernel.lib.utils import slugify

IntegrationTypes: typing.TypeAlias = typing.Literal["api", "database", "dataset"]

@dataclass(kw_only=True)
class Resource:
    resource_type: typing.ClassVar[str]
    integration: typing.Optional[str] = None
    # optional -- if not included on handwritten yaml, it will be generated
    resource_id: typing.Optional[str] = None
    def __post_init__(self):
        if self.resource_id is None:
            self.resource_id = str(uuid4())

@dataclass(kw_only=True)
class FileResource(Resource):
    resource_type: str = "file"
    # user facing name
    name: str
    # optional - None could be an unsaved new file held in memory but not on disk
    filepath: typing.Optional[str] = field(default=None)
    # TODO: encoding?
    content: typing.Optional[str] = field(default=None)

@dataclass(kw_only=True)
class ExampleResource(Resource):
    resource_type: str = "example"
    query: str
    code: str
    notes: typing.Optional[str] = field(default=None)

@dataclass
class IntegrationExample:
    query: str
    code: str
    notes: typing.Optional[str]

@dataclass
class Integration:
    name: str
    description: str
    provider: str
    resources: dict[str, Resource] = field(default_factory=lambda: {})
    uuid: str = field(default_factory=lambda: str(uuid4()))

    # created if not present -- UUID! but must be easily json serializable
    slug: typing.Optional[str] = field(default=None)
    datatype: IntegrationTypes = field(default="api")
    url: typing.Optional[str] = field(default=None)
    img_url: typing.Optional[str] = field(default=None)
    source: typing.Optional[str] = field(default=None)
    last_updated: typing.Optional[datetime|date] = field(default=None)

    @classmethod
    def slugify(cls, name: str):
        return slugify(name)

    def __post_init__(self):
        if self.slug is None:
            self.slug = self.slugify(self.name)

    def add_resources(self, resource_list: list[Resource]):
        for resource in resource_list:
            if resource.resource_id:
                self.resources[resource.resource_id] = resource
