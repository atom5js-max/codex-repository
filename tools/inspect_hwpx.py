from __future__ import annotations

import sys
import zipfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: inspect_hwpx.py <file.hwpx>")
        return 2

    path = Path(sys.argv[1])
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
