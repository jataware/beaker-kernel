import ast
import json
import logging
from typing import Any

from .base import BeakerSubkernel

logger = logging.getLogger(__name__)


def get_kernel_name():
    from jupyter_client.kernelspec import KernelSpecManager
    ksm = KernelSpecManager()
    kernel_specs = ksm.get_all_specs()
    for kernel, specs in kernel_specs.items():
        if specs.get("spec", {}).get("language", None) == "julia":
            return kernel
    return None


class JuliaSubkernel(BeakerSubkernel):
    DISPLAY_NAME = "Julia"
    SLUG = "julia"
    KERNEL_NAME = get_kernel_name()

    WEIGHT = 30

    @classmethod
    def parse_subkernel_return(cls, execution_result) -> Any:
        return_raw = execution_result.get("return")
        if return_raw:
            return_str = ast.literal_eval(return_raw)
            try:
                python_obj = json.loads(return_str)
            except json.JSONDecodeError:
                raise
            return python_obj
