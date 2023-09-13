import pandas as pd; import io
import time
output_buff = io.BytesIO()
{{ var_name|default("df") }}.to_csv(output_buff, index=False, header=True)
output_buff.seek(0)

for line in output_buff.getvalue().splitlines():
    print(line.decode())
