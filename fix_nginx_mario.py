#!/usr/bin/env python3
f = "/etc/nginx/sites-enabled/mt5-fxpro"
with open(f, "r") as fh:
    content = fh.read()

if "location /mario" in content:
    print("ALREADY EXISTS")
else:
    insert = '\n    location /mario {\n        root /opt;\n        index index.html;\n        try_files $uri $uri/ =404;\n    }\n'
    target = "    location = / {\n        return 301 /acuarela2;\n    }\n"
    content = content.replace(target, target + insert, 1)
    with open(f, "w") as fh:
        fh.write(content)
    print("UPDATED")
