import abc
from typing import Dict, Any
from ..codesets import get_template


class BaseSubkernel(abc.ABC):
    DISPLAY_NAME: str
    KERNEL_NAME: str
    DATAFRAME_TYPE_NAME: str


    def get_code(self, toolset_name: str, name: str, render_dict: Dict[str, Any]={}) -> str:
        return get_template(toolset_name, self.KERNEL_NAME, name, render_dict)

    @classmethod
    @abc.abstractmethod
    def parse_subkernel_return(cls, execution_result) -> Any:
        ...
