import copy
import json
import pandas as pd

_result = {}

for _var_name, _df in ((k, v) for k, v in copy.copy(locals()).items() if isinstance(v, pd.DataFrame) and not k.startswith("_")):
    _split_df = json.loads(_df.head(30).to_json(orient="split"))

    _result[_var_name] = {
        "columns": _split_df["columns"],
        "datatypes": str(_df.dtypes),
        "head": [_split_df["columns"]] + _split_df["data"],
        "statistics": str(_df.describe()),
    }

_result