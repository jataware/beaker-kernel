import typing
from dataclasses import dataclass, field, MISSING, asdict
from datetime import datetime, date

DatasourceTypes: typing.TypeAlias = typing.Literal["api", "database", "dataset"]

@dataclass
class DatasourceAttachment:
    # user facing name
    name: str

    # optional - None could be an unsaved new file held in memory but not on disk
    filepath: typing.Optional[str] = field(default=None)
    # if None - either zero-byte file or content to load at some point in the future
    content: typing.Optional[bytes] = field(default=None)
    # disambiguation for the above field
    is_empty_file: bool = field(default=False)
    # TODO: encoding?

@dataclass 
class DatasourceExample:
    query: str
    code: str
    notes: typing.Optional[str]

@dataclass
class Datasource:
    slug: str
    name: str
    description: str

    datatype: DatasourceTypes = field(default="api")
    url: typing.Optional[str] = field(default=None)
    img_url: typing.Optional[str] = field(default=None)
    source: typing.Optional[str] = field(default=None)
    last_updated: typing.Optional[datetime|date] = field(default=None)
    attached_files: typing.Optional[list[DatasourceAttachment]] = field(default=None)
    # currently o(n) example lookup as a list rather than k,v map with query as key.
    # should be changed eventually, but left for backwards compatibility
    examples: typing.Optional[list[DatasourceExample]] = field(default=None)