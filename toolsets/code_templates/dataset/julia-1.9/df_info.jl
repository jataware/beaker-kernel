JSON.json(Dict(
    "head" => string(first(df,15)),
    "columns" => string(names(df)),
    "dtypes" => string(eltype.(eachcol(df))),
    "statistics" => string(describe(df)),
)) |> DisplayAs.unlimited
