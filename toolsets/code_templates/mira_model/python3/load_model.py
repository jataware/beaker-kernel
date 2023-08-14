amr = requests.get("{{ model_url }}").json()
{{ var_name }} = template_model_from_askenet_json(amr)
