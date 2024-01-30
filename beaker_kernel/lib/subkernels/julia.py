import ast
import json
import logging
from typing import Any

from .base import BaseSubkernel

logger = logging.getLogger(__name__)


class JuliaSubkernel(BaseSubkernel):
    DISPLAY_NAME = "Julia"
    SLUG = "julia"
    KERNEL_NAME = "julia-1.9"

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
