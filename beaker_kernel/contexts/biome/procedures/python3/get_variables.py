import inspect
"\n".join(
    f"variable `{var_name}`\n  type: {type(var_value)}\n  class: {var_value.__name__ if inspect.isclass(var_value) else var_value.__class__.__name__}"
    for var_name, var_value
    in locals().items()
    if not var_name.startswith("_")
    and var_name not in ("In", "Out", "get_ipython", "exit", "quit")  # Skip variables added by Jupyter
    and not inspect.ismodule(var_value)  # Skip imported modules, as they are modules, not "variables"
)
