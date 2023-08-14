output_buff = IOBuffer()
CSV.write(output_buff, df, writeheader=true)

seekstart(output_buff)

for line in readlines(output_buff)
    println(line)
end
