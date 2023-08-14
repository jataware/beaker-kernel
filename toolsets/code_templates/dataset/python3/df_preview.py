import json
split_df = json.loads(df.head(30).to_json(orient="split"))

{
    "name": "Temp dataset (not saved)",
    "headers": split_df["columns"],
    "csv": [split_df["columns"]] + split_df["data"],
}
