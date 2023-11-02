using SyntacticModels, Decapodes, Catlab
import JSON3, DisplayAs

{{ var_name|default("_expr") }} = Decapodes.parse_decapode(quote
    {{ declaration }}
end)
