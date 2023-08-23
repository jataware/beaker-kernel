amr = requests.get("{{ model_url }}").json()
{{ var_name|default("df") }} = template_model_from_askenet_json(amr)
