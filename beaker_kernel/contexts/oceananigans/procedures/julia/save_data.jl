import HTTP, JSON3, DisplayAs

_DATA_SERVICE_URL = "{{ dataservice_url }}" 
_DATASET_NAME = "{{ name }}"
_DATASET_DESCRIPTION = "{{ description }}"
_FILENAMES = split("{{ filenames }}", ",")


_dataset = Dict(
    "name" => _DATASET_NAME,
    "description" => _DATASET_DESCRIPTION,
    "file_names" => _FILENAMES
)

_create_req = HTTP.post("$_DATA_SERVICE_URL/datasets", body=JSON3.write(_dataset))
_new_dataset_id = JSON3.read(String(_create_req.body))["id"]

for filename in _FILENAMES 
    _new_dataset_url = "$_DATA_SERVICE_URL/datasets/$_new_dataset_id"
    _data_url_req = HTTP.get("$(_new_dataset_url)/upload-url?filename=$filename")
    _data_url = get!(JSON3.read(String(_data_url_req.body)), "url", nothing)
    _filesize = stat(filename).size
    _upload_response = HTTP.put(_data_url, ["content-length" => _filesize], open(filename, "r"))
    if _upload_response.status != 200
        error("Error uploading dataframe: $(String(_upload_response.body))")
    end

end

_result = Dict("dataset_id" => _new_dataset_id)
JSON3.write(_result) |> DisplayAs.unlimited