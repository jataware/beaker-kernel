import ast
from typing import Any

from .base import CheckpointableBeakerSubkernel, Checkpoint

import logging
logger = logging.getLogger(__name__)


class PythonSubkernel(CheckpointableBeakerSubkernel):
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

    async def generate_checkpoint_from_state(self) -> Checkpoint:
        save_state_code = """
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

_result = {}
for _name, _value in dict(locals()).items():
    if _name.startswith('_') or _name in ('In', 'Out', 'get_ipython', 'exit', 'quit', 'open'):
        continue
    _path = f"%s/{_name}.pkl"
    with open(_path, "wb") as _f:
        try:
            _dill.dump(_value, _f)
        except Exception as e:
            continue
        _result[_name] = _path

_result = _json.loads(_json.dumps(_result, cls=_SubkernelStateEncoder))
del _inspect, _json, _dill
_result
""" % self.storage_prefix
        response = await self.context.evaluate(save_state_code)
        return response["return"]


    async def load_checkpoint(self, checkpoint: Checkpoint):
        vars = await self.context.evaluate("""
import dill as _dill
_exclusion_critieria = lambda name: name.startswith('_') or name in ('In', 'Out', 'get_ipython', 'exit', 'quit', 'open')
[ name for name, value in dict(locals()).items() if not _exclusion_critieria(name) ]
""")
        await self.context.execute(f"del {', '.join(vars['return'])}")
        deserialization_code = ""
        for varname, filename in checkpoint.items():
            deserialization_code += f"""

with open("{filename}", "rb") as _file:
    {varname} = _dill.load(_file)

"""
        deserialization_code += "del _dill"
        await self.context.execute(deserialization_code)

    async def setup(self):
        setup_code = f"""
import importlib
import os
import site
import sys
if site.USER_SITE not in sys.path:
    os.makedirs(site.USER_SITE, exist_ok=True)
    sys.path.append(site.USER_SITE)
    importlib.invalidate_caches()
del importlib, os, site, sys
"""
        await self.context.execute(setup_code)
