# TODO: Rename file `decapode_to_info.jl`
using Decapodes, Catlab, Catlab.Graphics
import JSON3, DisplayAs

function decapode_to_svg(d)
    io = IOBuffer()
    Catlab.Graphics.Graphviz.run_graphviz(io, to_graphviz(d), format="svg")
    String(take!(io))
end


_response = Dict(
    "json" => {{ var_name|default("model") }} |> Decapodes.Term,
    "image" => decapode_to_svg({{ var_name|default("model") }}) 
    # {{ var_name|default("model") }} ∘ bytes ∘ gen_image
)
_response |> DisplayAs.unlimited ∘ JSON3.write