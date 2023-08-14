df = DataFrame(CSV.File(IOBuffer(HTTP.get("{{ data_url }}").body)))
