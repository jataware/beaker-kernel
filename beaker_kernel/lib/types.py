import typing
from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID, uuid4

IntegrationTypes: typing.TypeAlias = typing.Literal["api", "database", "dataset"]

@dataclass(kw_only=True)
class Resource:
    resource_type: typing.ClassVar[str]
    integration: typing.Optional[str] = None
    # optional -- if not included on handwritten yaml, it will be generated
    resource_id: typing.Optional[UUID] = None
    def __post_init__(self):
        if self.resource_id is None:
            self.resource_id = uuid4()

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
class Integration:
    name: str
    description: str
    provider: str

    # created if not present -- UUID! but must be easily json serializable
    slug: typing.Optional[str] = field(default=None)
    datatype: IntegrationTypes = field(default="api")
    url: typing.Optional[str] = field(default=None)
    img_url: typing.Optional[str] = field(default=None)
    source: typing.Optional[str] = field(default=None)
    last_updated: typing.Optional[datetime|date] = field(default=None)

    def __post_init__(self):
        if self.slug is None:
            self.slug = str(uuid4())
