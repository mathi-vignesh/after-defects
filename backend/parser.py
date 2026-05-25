"""
RIFX parser for After Effects .aep and .ffx files.

CONFIRMED format (real file analysis + open-source reference):
  Byte layout:
    [0x00-0x03]  "RIFX" magic
    [0x04-0x07]  root chunk size (big-endian u32)
    [0x08-0x0b]  "Egg!" form type
    [0x0c-0x0f]  "svap" chunk id       (first sub-chunk)
    [0x10-0x13]  svap chunk size
    [0x14-0x17]  svap data
    [0x18-0x1b]  "head" chunk id       (second sub-chunk)
    [0x1c-0x1f]  head chunk size
    [0x20-0x33]  head chunk data (20 bytes)

  Version byte = content[33] = head_data[1]
  Formula: version = byte - 0x5b + 20
  e.g. 0x5e (94) → 94 - 91 + 20 = 23 → AE 2023
"""

import struct
from dataclasses import dataclass
from versions import get_version_by_byte, get_closest_version, byte_to_ver

RIFX_MAGIC = b"RIFX"
AEP_FORM   = b"Egg!"
FFX_FORM   = b"FaFX"

HEAD_CHUNK_EXPECTED_OFFSET = 0x18
VERSION_BYTE_OFFSET        = 33   # content[33] = head_data[1]


@dataclass
class VersionInfo:
    version_byte:   int
    version_ver:    int   # AE major version number (e.g. 23)
    version_hex:    str
    version_name:   str
    version_short:  str
    version_year:   int
    app_ver:        str
    is_exact_match: bool
    file_type:      str
    head_data:      bytes  # full 20-byte head chunk data for patching


class RIFXParseError(Exception):
    pass


def parse_aep(data: bytes) -> VersionInfo:
    if len(data) < 52:
        raise RIFXParseError("File too small to be a valid AEP/FFX (need at least 52 bytes).")

    if data[:4] != RIFX_MAGIC:
        raise RIFXParseError(
            f"Not a RIFX file (magic={data[:4]!r}). Upload a valid .aep or .ffx file."
        )

    form_type = data[8:12]
    file_type = "ffx" if form_type == FFX_FORM else "aep"

    # Find head chunk — should be at 0x18, but scan if not
    head_offset = _find_head_chunk(data)
    if head_offset is None:
        raise RIFXParseError("Could not locate the 'head' chunk.")

    head_data_start  = head_offset + 8       # skip 4-byte id + 4-byte size
    head_data        = data[head_data_start:head_data_start + 20]
    ver_byte_offset  = head_data_start + 1   # head_data[1]
    version_byte     = data[ver_byte_offset]

    exact = get_version_by_byte(version_byte)
    info  = exact or get_closest_version(version_byte)

    if info is None:
        raise RIFXParseError(f"Unknown version byte: 0x{version_byte:02x}")

    return VersionInfo(
        version_byte   = version_byte,
        version_ver    = byte_to_ver(version_byte),
        version_hex    = f"0x{version_byte:02x}",
        version_name   = info["name"] if exact else f"Unknown (near {info['name']})",
        version_short  = info["short"],
        version_year   = info["year"],
        app_ver        = info["app_ver"],
        is_exact_match = exact is not None,
        file_type      = file_type,
        head_data      = head_data,
    )


def _find_head_chunk(data: bytes):
    """Return the offset of the 'head' chunk header, or None."""
    # Check expected position first
    if data[HEAD_CHUNK_EXPECTED_OFFSET:HEAD_CHUNK_EXPECTED_OFFSET+4] == b"head":
        return HEAD_CHUNK_EXPECTED_OFFSET
    # Scan first 512 bytes
    offset = 12
    while offset + 8 <= min(512, len(data)):
        chunk_id   = data[offset:offset+4]
        chunk_size = struct.unpack_from(">I", data, offset+4)[0]
        if chunk_id == b"head":
            return offset
        advance = 8 + chunk_size
        if advance % 2: advance += 1
        if advance < 8: break
        offset += advance
    return None
