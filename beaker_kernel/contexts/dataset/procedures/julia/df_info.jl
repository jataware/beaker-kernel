_result = Dict()
_var_syms = names(Main)

for _var_sym in _var_syms
    _var = eval(_var_sym)
    if typeof(_var) == DataFrame
        _data = [Array(_r) for _r=eachrow(first(_var, 30))]
        _result["$(_var_sym)"] = Dict(
            "columns" => names(_var),
            "head" => _data,
            "datatypes" => string(eltype.(eachcol(_var))),
            "statistics" => string(describe(_var)),
        )
    end
end

JSON3.write(_result) |> DisplayAs.unlimited
