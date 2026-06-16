from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from revise_gs_hwpx import serialize_hwpx_xml, write_hwpx


src = Path(sys.argv[1])
dst = Path(sys.argv[2])
with zipfile.ZipFile(src) as zf:
    header = ET.fromstring(zf.read("Contents/header.xml"))
    section = ET.fromstring(zf.read("Contents/section0.xml"))
write_hwpx(src, dst, serialize_hwpx_xml(header), serialize_hwpx_xml(section))
print(dst)
