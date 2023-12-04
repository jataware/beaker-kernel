from IPython.core.interactiveshell import InteractiveShell;
from IPython.core import display_functions;
from mira.modeling.amr.petrinet import template_model_to_petrinet_json

format_dict, md_dict = InteractiveShell.instance().display_formatter.format(GraphicalModel.for_jupyter(model))
result = {
    "application/json": template_model_to_petrinet_json(model)
}
for key, value in format_dict.items():
    if "image" in key:
        result[key] = value

result
