import pydoc
try:
    import {{module}}
    return_value = pydoc.plaintext.document({{target}})
except ImportError as err:
    return_value = """
There was an error importing module `{{module}}`. It is probably not a valid target for import.
Please check the list of installed modules and try again.
    """.trim()
except AttributeError as err:
    package_info = _get_map({{target}})
    return_value = f"""
    Targeted item `{{target}}` could not be found. Below is a map of the contents of module `{{module}}`.
    Please review the list and try again if a suitable option is found or report this issue to the user if not.

    {package_info}
    """.trim()

return_value
