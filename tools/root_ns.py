from __future__ import annotations

import re
import sys
import zipfile


with zipfile.ZipFile(sys.argv[1]) as zf:
    for name in ["Contents/section0.xml", "Contents/header.xml"]:
        text = zf.read(name).decode("utf-8")
        root_start = text.find("<", text.find("?>") + 2)
        tag = text[root_start : text.find(">", root_start) + 1]
        print("---", name)
        for match in re.findall(r'xmlns(?::[^=]+)?="[^"]+"', tag):
            print(match)
