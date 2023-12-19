import pydoc
try:
    import {{module}}
    pydoc.getdoc({{target}})
except ImportError:
    """
There was an error importing module `{{module}}`. It is probably not a valid target for import.
Please check the list of installed modules and try again.
    """.trim()
