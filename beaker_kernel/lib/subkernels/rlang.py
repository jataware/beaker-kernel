import ast
import json
import logging
import re
from typing import Any

from .base import BaseSubkernel

logger = logging.getLogger(__name__)


class RSubkernel(BaseSubkernel):
    DISPLAY_NAME = "R"
    SLUG = "rlang"
    KERNEL_NAME = "ir"
    DATAFRAME_TYPE_NAME = "data.frame"

    @classmethod
    def parse_subkernel_return(cls, execution_result) -> Any:
        # irkernel annoyingly does not return the last item in the code execution as the "return" item, so we print the response as part of the output
        return_raw = "".join(execution_result.get("stdout_list"))
        # Even more annoyingly, irkernel includes the [#] thing to show the execution number in the output, so we have to strip it out
        return_raw = re.sub(r'^\[\d*\]\s*', '', return_raw)
        if return_raw:
            return_str = ast.literal_eval(return_raw)
            try:
                python_obj = json.loads(return_str)
            except json.JSONDecodeError:
                raise
            return python_obj
