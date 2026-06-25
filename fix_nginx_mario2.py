#!/usr/bin/env python3
f = "/etc/nginx/sites-enabled/00-main-ip.conf"
with open(f, "r") as fh:
    content = fh.read()

if "location /mario" in content:
    print("ALREADY EXISTS")
else:
    mario_block = '\n    location /mario {\n        root /opt;\n        index index.html;\n        try_files $uri $uri/ =404;\n    }\n'
    # Insert before the closing } of the server block (last occurrence)
    target = '\n    location = / {\n        root /opt/mario;\n        index index.html;\n    }\n}'
    replacement = '\n    location /mario {\n        root /opt;\n        index index.html;\n        try_files $uri $uri/ =404;\n    }\n\n    location = / {\n        root /opt/mario;\n        index index.html;\n    }\n}'
    content = content.replace(target, replacement, 1)
    with open(f, "w") as fh:
        fh.write(content)
    print("UPDATED")
