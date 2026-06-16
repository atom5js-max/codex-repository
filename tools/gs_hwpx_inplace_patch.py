from __future__ import annotations

import binascii
import random
import struct
import sys
import zlib
from pathlib import Path
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gs_hwpx_revise_safe as safe


WORKSPACE = Path(__file__).resolve().parents[1]
TARGET = "Contents/section0.xml"
OUTPUT_NAME = "(벽진바이오텍)_FEMS플러스_사업계획서_GS시스템_중복정리본_원본ZIP패치.hwpx"


def raw_deflate(data: bytes, level: int = 9) -> bytes:
    co = zlib.compressobj(level, zlib.DEFLATED, -15)
    return co.compress(data) + co.flush()


def pad_xml_to_len(xml: str, target_len: int, seed: int) -> bytes:
    base = xml.encode("utf-8")
    if len(base) > target_len:
        raise ValueError("patched XML is longer than original")
    need = target_len - len(base)
    if need == 0:
        return base
    if need < 7:
        pad = " " * need
    else:
        rng = random.Random(seed)
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        body_len = need - len("<!---->")
        body = "".join(rng.choice(alphabet) for _ in range(body_len))
        pad = "<!--" + body + "-->"
    insert = xml.rfind("</hs:sec>")
    if insert == -1:
        raise ValueError("section closing tag not found")
    return (xml[:insert] + pad + xml[insert:]).encode("utf-8")


def locate_local_entry(data: bytes, filename: str) -> tuple[int, int, int, int, int]:
    pos = 0
    while pos + 30 <= len(data):
        sig = data[pos : pos + 4]
        if sig == b"PK\x03\x04":
            name_len = struct.unpack_from("<H", data, pos + 26)[0]
            extra_len = struct.unpack_from("<H", data, pos + 28)[0]
            comp_size = struct.unpack_from("<I", data, pos + 18)[0]
            uncomp_size = struct.unpack_from("<I", data, pos + 22)[0]
            name = data[pos + 30 : pos + 30 + name_len].decode("utf-8")
            payload_start = pos + 30 + name_len + extra_len
            if name == filename:
                return pos, payload_start, comp_size, uncomp_size, name_len
            pos = payload_start + comp_size
            continue
        if sig in (b"PK\x01\x02", b"PK\x05\x06"):
            break
        pos += 1
    raise ValueError(f"local entry not found: {filename}")


def patch_central(data: bytearray, filename: str, crc: int) -> None:
    pos = data.find(b"PK\x01\x02")
    while pos != -1 and pos + 46 <= len(data) and data[pos : pos + 4] == b"PK\x01\x02":
        name_len = struct.unpack_from("<H", data, pos + 28)[0]
        extra_len = struct.unpack_from("<H", data, pos + 30)[0]
        comment_len = struct.unpack_from("<H", data, pos + 32)[0]
        name = data[pos + 46 : pos + 46 + name_len].decode("utf-8")
        if name == filename:
            struct.pack_into("<I", data, pos + 16, crc)
            return
        pos = pos + 46 + name_len + extra_len + comment_len
    raise ValueError(f"central entry not found: {filename}")


def main() -> None:
    source = next(path for path in WORKSPACE.glob("*.hwpx") if "v3.1" in path.name)
    output = WORKSPACE / OUTPUT_NAME
    original_bytes = bytearray(source.read_bytes())

    with zipfile.ZipFile(source) as z:
        info = z.getinfo(TARGET)
        original_xml = z.read(TARGET).decode("utf-8")

    patched_xml, changed, blanked = safe.patch_section_xml(original_xml)

    best: tuple[int, bytes, bytes] | None = None
    for seed in range(200):
        candidate_xml = pad_xml_to_len(patched_xml, info.file_size, seed)
        compressed = raw_deflate(candidate_xml, 9)
        if len(compressed) <= info.compress_size:
            best = (seed, candidate_xml, compressed)
            break
    if best is None:
        raise RuntimeError("could not fit compressed patched section into original stream size")

    seed, candidate_xml, compressed = best
    # ZIP readers ignore trailing bytes after a complete deflate stream because the
    # compressed size is fixed in the header. Pad with zero bytes to preserve layout.
    compressed = compressed + (b"\x00" * (info.compress_size - len(compressed)))
    crc = binascii.crc32(candidate_xml) & 0xFFFFFFFF

    local_pos, payload_start, comp_size, uncomp_size, _ = locate_local_entry(original_bytes, TARGET)
    if comp_size != info.compress_size or uncomp_size != info.file_size:
        raise RuntimeError("local header sizes differ from central directory")
    original_bytes[payload_start : payload_start + comp_size] = compressed
    struct.pack_into("<I", original_bytes, local_pos + 14, crc)
    patch_central(original_bytes, TARGET, crc)
    output.write_bytes(original_bytes)

    print(f"output={output}")
    print(f"changed={changed} blanked={blanked} seed={seed}")
    print(f"section_uncompressed={len(candidate_xml)} section_compressed={len(compressed)} crc={crc}")


if __name__ == "__main__":
    main()
