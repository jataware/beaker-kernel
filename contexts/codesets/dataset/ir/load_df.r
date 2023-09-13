{% for var_name, data_url in var_map.items() -%}
{{ var_name }} = read.csv("{{ data_url }}")
{% endfor %}
