import inspect
import pydoc
_output = []
for _var_name in ["{{ variable_name }}"]:
    _var = locals().get(_var_name)
    _output.append(
        f"""
{_var_name}:
  type: {type(_var)}
  repr: {repr(_var)}
  help_synopsis: {pydoc.splitdoc(pydoc.getdoc(_var))[0]}
  class: {_var.__name__ if inspect.isclass(_var) else _var.__class__.__name__}
        """.strip()
    )

"\n".join(_output)
