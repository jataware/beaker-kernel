parent_url = "$(dataservice_url)/datasets/$(parent_dataset_id)"
response = HTTP.get(parent_url)
parent_dataset = JSON.parse(String(response.body))

if isempty(parent_dataset)
    error("Unable to locate parent dataset '$(parent_dataset_id)'")
end

new_dataset = deepcopy(parent_dataset)
delete!(new_dataset, "id")
new_dataset["name"] = new_name
new_dataset["description"] *= "\nTransformed from dataset '$(parent_dataset["name"])' ($(parent_dataset["id"])) at $(Dates.format(Dates.now(), "c U"))"
new_dataset["file_names"] = [filename]

create_req = HTTP.post("$(dataservice_url)/datasets", body=JSON.json(new_dataset))
new_dataset_id = JSON.parse(String(create_req.body))["id"]

new_dataset["id"] = new_dataset_id
new_dataset_url = "$(dataservice_url)/datasets/$(new_dataset_id)"
data_url_req = HTTP.get("$(new_dataset_url)/upload-url?filename=$(filename)")
data_url = JSON.parse(String(data_url_req.body)).get("url", nothing)

temp_csv_file = tempname()
CSV.write(temp_csv_file, df, writeheader=true)
upload_response = HTTP.put(data_url, open(temp_csv_file, "r"))

if upload_response.status != 200
    error("Error uploading dataframe: $(String(upload_response.body))")
end

# Cleanup
rm(temp_csv_file)

Dict("dataset_id" => new_dataset_id)
