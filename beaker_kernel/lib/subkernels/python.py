import ast
from typing import Any

from .base import BaseSubkernel


class PythonSubkernel(BaseSubkernel):
    DISPLAY_NAME = "Python 3"
    SLUG = "python3"
    KERNEL_NAME = "python3"

    WEIGHT = 20

    import json
    json.JSONEncoder

    FETCH_STATE_CODE: str = """
import inspect as _inspect
import json as _json
class _SubkernelStateEncoder(_json.JSONEncoder):
    def default(self, o):
        # if callable(o):
            # return f"Function named"
            # return super().default(o)
        try:
            return super().default(o)
        except:
            return str(o)

_result = {
    "modules": {},
    "variables": {},
    "functions": {},
}
for _name, _value in dict(locals()).items():
    if _name.startswith('_') or _name in ('In', 'Out', 'get_ipython', 'exit', 'quit', 'open'):
        continue
    if callable(_value):
        _result["functions"][_name] = str(_value)
    elif _inspect.ismodule(_value):
        _result["modules"][_name] = str(_value)
    else:
        _result["variables"][_name] = _value

_result = _json.loads(_json.dumps(_result, cls=_SubkernelStateEncoder))
_result
"""

    @classmethod
    def parse_subkernel_return(cls, execution_result) -> Any:
        return_str = execution_result.get("return")
        if return_str:
            python_obj = ast.literal_eval(return_str)
            return python_obj
