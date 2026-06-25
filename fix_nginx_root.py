#!/usr/bin/env python3
f = "/etc/nginx/sites-enabled/00-main-ip.conf"
with open(f, "r") as fh:
    content = fh.read()

# Cambiar location = / de servir archivo (que falla por redirect interno) a redirect a /mario/
old = "    location = / {\n        root /opt/mario;\n        index index.html;\n    }\n"
new = "    location = / {\n        return 301 /mario/;\n    }\n"

if old in content:
    content = content.replace(old, new, 1)
    with open(f, "w") as fh:
        fh.write(content)
    print("UPDATED")
else:
    print("PATTERN NOT FOUND - current content around location = /:")
    idx = content.find("location = / {")
    print(repr(content[idx-5:idx+100]))
