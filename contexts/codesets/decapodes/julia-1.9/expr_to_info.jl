using SyntacticModels, Decapodes, Catlab
import JSON3, DisplayAs

function expr_to_svg(expr)
    io = IOBuffer()
    Catlab.Graphics.Graphviz.run_graphviz(io, to_graphviz(Decapodes.SummationDecapode(expr)), format="svg")
    String(take!(io))
end

_response = Dict(
    "application/json" => {{ var_name|default("_expr") }},
    "image/svg" => expr_to_svg({{ var_name|default("_expr") }})
)
_response |> DisplayAs.unlimited ∘ JSON3.write
