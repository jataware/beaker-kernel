import copy
{{ var_name|default("model") }} = copy.deepcopy(_model_orig)
