from mira.metamodel.ops import stratify

{{ var_name|default("model") }} = stratify(
    template_model={{ var_name|default("model") }},
    **{{ stratify_kwargs }}
)
