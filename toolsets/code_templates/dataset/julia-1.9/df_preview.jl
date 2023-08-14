_split_df = first(df, 30)
_headers = names(_split_df)
_data = [Array(_r) for _r=eachrow(_split_df)]

JSON.json(Dict(
    "name" => "Temp dataset (not saved)",
    "headers" => _headers,
    "csv" => vcat([_headers], _data),
)) |> DisplayAs.unlimited
