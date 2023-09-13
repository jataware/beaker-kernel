from IPython.core.interactiveshell import InteractiveShell;
from IPython.core import display_functions;
InteractiveShell.instance().display_formatter.format(GraphicalModel.for_jupyter(model))
