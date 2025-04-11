import typing
from dataclasses import dataclass, field, MISSING, asdict
from datetime import datetime, date

typing.TypedDict

DatasourceTypes: typing.TypeAlias = typing.Literal["api", "database", "dataset"]

@dataclass
class Datasource:
    uid_or_slug: str
    name: str
    description: str

    datatype: DatasourceTypes = field(default="api")
    url: typing.Optional[str] = field(default=None)
    img_url: typing.Optional[str] = field(default=None)
    source: typing.Optional[str] = field(default=None)
    last_updated: typing.Optional[datetime|date] = field(default=None)
