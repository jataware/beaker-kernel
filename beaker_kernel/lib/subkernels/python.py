import ast
from typing import Any

from .base import BaseSubkernel, Checkpoint

class PythonSubkernel(BaseSubkernel):
    DISPLAY_NAME = "Python 3"
    SLUG = "python3"
    KERNEL_NAME = "python3"

    WEIGHT = 20

    SERIALIZATION_EXTENSION = "pickle"


    import json
    json.JSONEncoder

    FETCH_STATE_CODE: str = """
import inspect as _inspect
import json as _json
import dill as _dill
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

#     def get_current_checkpoint(self) -> Checkpoint:
#         save_state_code = """
# import inspect as _inspect
# import json as _json
# import dill as _dill
# class _SubkernelStateEncoder(_json.JSONEncoder):
#     def default(self, o):
#         # if callable(o):
#             # return f"Function named"
#             # return super().default(o)
#         try:
#             return super().default(o)
#         except:
#             return str(o)

# _result = {}
# for _name, _value in dict(locals()).items():
#     if _name.startswith('_') or _name in ('In', 'Out', 'get_ipython', 'exit', 'quit', 'open'):
#         continue
#     _path = f"%s/{_name}.pkl"
#     with open(_path, "wb") as f:
#        _dill.dump(_value, f)
#        _result[_name] = _path

# _result = _json.loads(_json.dumps(_result, cls=_SubkernelStateEncoder))
# del _inspect, _json, _dill
# _result
# """ % self.storage_prefix
#         return self.beaker_kernel.evaluate(save_state_code)
        

#     def load_checkpoint(self, checkpoint: Checkpoint):
#         self.beaker_kernel.evaluate("import dill as _dill")
#         for varname, filename in checkpoint.items():
#             load_state_code = f"""
# import dill as _dill
# with open({filename}, "rb") as file:
#     {varname} = _dill.load(file))
# """ 
#             self.beaker_kernel.evaluate(load_state_code)
#         self.beaker_kernel.evaluate("del _dill")
        