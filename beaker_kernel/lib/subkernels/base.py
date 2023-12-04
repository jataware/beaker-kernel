import abc
from typing import Any, Dict

from beaker_kernel.lib.codeset import get_template


class BaseSubkernel(abc.ABC):
    DISPLAY_NAME: str
    SLUG: str
    KERNEL_NAME: str

    def get_code(self, codeset_name: str, name: str, render_dict: Dict[str, Any]={}) -> str:
        return get_template(codeset_name, self.KERNEL_NAME, name, render_dict)

    @classmethod
    @abc.abstractmethod
    def parse_subkernel_return(cls, execution_result) -> Any:
        ...
