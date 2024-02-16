import abc
import json
from typing import Any

class JsonStateEncoder(json.JSONEncoder):
    pass

class BaseSubkernel(abc.ABC):
    DISPLAY_NAME: str
    SLUG: str
    KERNEL_NAME: str

    WEIGHT: int = 50  # Used for auto-sorting in drop-downs, etc. Lower weights are listed earlier.

    FETCH_STATE_CODE: str = ""

    @classmethod
    @abc.abstractmethod
    def parse_subkernel_return(cls, execution_result) -> Any:
        ...
