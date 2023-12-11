using SyntacticModels, Decapodes, Catlab
import JSON3, DisplayAs

function expr_to_svg(model)
    _path = "/tmp/decapode.json"
    open(_path, "w") do f
        io = IOBuffer()
        Catlab.Graphics.Graphviz.run_graphviz(io, to_graphviz(model), format="svg")
    end
    open(_path, "r") do f
        return String(take!(f))
    end
end

_response = Dict(
    "application/json" => generate_json_acset({{ target }}),
    # "image/svg" => expr_to_svg({{ target }}) # TODO: Reinclude when graphviz bug is fixed
)



_response |> DisplayAs.unlimited ∘ JSON3.write
