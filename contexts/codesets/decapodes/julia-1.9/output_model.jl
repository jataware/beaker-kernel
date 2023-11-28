# TODO: Rename file `decapode_to_info.jl`
using Decapodes, Catlab, Catlab.Graphics
import JSON3, DisplayAs

function decapode_to_svg(d)
    io = IOBuffer()
    Catlab.Graphics.Graphviz.run_graphviz(io, to_graphviz(d), format="svg")
    String(take!(io))
end

_response = []
for model in [{{ var_names }}] 
    _item = Dict(
        "application/json" => model |> Decapodes.Term,
        "image/svg" => decapode_to_svg(model) 
        # {{ var_name|default("model") }} ∘ bytes ∘ gen_image
    )
    push!(_response, _item)

end
_response |> DisplayAs.unlimited ∘ JSON3.write