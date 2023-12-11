{% for var_name, data_url in var_map.items() -%}
{{ var_name|default("df") }} = DataFrame(CSV.File(IOBuffer(HTTP.get("{{ data_url }}").body)))
{% endfor %}
