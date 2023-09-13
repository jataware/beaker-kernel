_output_buff = IOBuffer()
CSV.write(_output_buff, {{ var_name|default("df") }}, writeheader=true)

seekstart(_output_buff)

for _line in readlines(_output_buff)
    println(_line)
end
