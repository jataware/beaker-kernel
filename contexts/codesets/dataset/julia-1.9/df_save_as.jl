using Dates

_parent_url = "{{dataservice_url}}/datasets/{{parent_dataset_id}}"
_response = HTTP.get(_parent_url)
_parent_dataset = JSON3.read(String(_response.body))

if isempty(_parent_dataset)
    error("Unable to locate parent dataset '{{ parent_dataset_id }}'")
end

_new_dataset = deepcopy(_parent_dataset)
delete!(_new_dataset, "id")
_new_dataset["name"] = "{{ new_name }}"
_new_dataset["description"] *= "\nTransformed from dataset '$(_parent_dataset["name"])' ($(_parent_dataset["id"])) at $(Dates.format(Dates.now(), "c U"))"
_new_dataset["file_names"] = ["{{ filename }}"]

_create_req = HTTP.post("{{ dataservice_url }}/datasets", body=JSON3.write(_new_dataset))
_new_dataset_id = JSON3.read(String(_create_req.body))["id"]

_new_dataset["id"] = _new_dataset_id
_new_dataset_url = "{{ dataservice_url }}/datasets/$(_new_dataset_id)"
_data_url_req = HTTP.get("$(_new_dataset_url)/upload-url?filename={{ filename }}")
_data_url = get!(JSON3.read(String(_data_url_req.body)), "url", nothing)

_temp_csv_file = tempname()
CSV.write(_temp_csv_file, {{ var_name|default("df") }}, writeheader=true)
_filesize = stat(_temp_csv_file).size
_upload_response = HTTP.put(_data_url, ["content-length" => _filesize], open(_temp_csv_file, "r"))

if _upload_response.status != 200
    error("Error uploading dataframe: $(String(_upload_response.body))")
end

# Cleanup
rm(_temp_csv_file)

_result = Dict("dataset_id" => _new_dataset_id)
JSON3.write(_result) |> DisplayAs.unlimited