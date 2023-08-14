import copy
import datetime
import requests
import tempfile

parent_url = f"{dataservice_url}/datasets/{parent_dataset_id}"
parent_dataset = requests.get(parent_url).json()
if not parent_dataset:
    raise Exception(f"Unable to locate parent dataset '{parent_dataset_id}'")

new_dataset = copy.deepcopy(parent_dataset)
del new_dataset["id"]
new_dataset["name"] = "{new_name}"
new_dataset["description"] += f"\\nTransformed from dataset '{parent_dataset['name']}' ({parent_dataset['id']}) at {datetime.datetime.utcnow().strftime('%c %Z')}"
new_dataset["file_names"] = ["{filename}"]

create_req = requests.post(f"{dataservice_url}/datasets", json=new_dataset)
new_dataset_id = create_req.json()["id"]

new_dataset["id"] = new_dataset_id
new_dataset_url = f"{dataservice_url}/datasets/{new_dataset_id}"
data_url_req = requests.get(f'{new_dataset_url}/upload-url?filename={filename}')
data_url = data_url_req.json().get('url', None)

# Saving as a temporary file instead of a buffer to save memory
with tempfile.TemporaryFile() as temp_csv_file:
    df.to_csv(temp_csv_file, index=False, header=True)
    temp_csv_file.seek(0)
    upload_response = requests.put(data_url, data=temp_csv_file)
if upload_response.status_code != 200:
    raise Exception(f"Error uploading dataframe: {upload_response.content}")

{
    "dataset_id": new_dataset_id,
}
