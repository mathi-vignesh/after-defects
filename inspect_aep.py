#!/usr/bin/env python3
"""
AEP/FFX Inspector — reverse engineering tool
Run this on a real .aep file to see the exact binary structure.

Usage:
    python3 inspect_aep.py yourfile.aep
    python3 inspect_aep.py yourfile.aep --hex-dump  # also dump raw bytes of each chunk
"""

import sys
import struct
import argparse
from pathlib import Path


def u32be(data, offset):
    return struct.unpack_from(">I", data, offset)[0]

def u16be(data, offset):
    return struct.unpack_from(">H", data, offset)[0]

def u32le(data, offset):
    return struct.unpack_from("<I", data, offset)[0]

def safe_fourcc(b):
    try:
        s = b.decode("latin-1")
        return "".join(c if 32 <= ord(c) < 127 else f"\\x{ord(c):02x}" for c in s)
    except:
        return b.hex()

def hex_preview(data, n=32):
    chunk = data[:n]
    hexpart = " ".join(f"{b:02x}" for b in chunk)
    ascpart = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    return f"{hexpart:<{n*3}}  |{ascpart}|"


LIST_CHUNKS = {b"LIST", b"RIFX", b"RIFF"}
VERSION_CHUNK_IDS = [b"tdsn", b"cdta", b"alas", b"EgTD", b"head", b"vers"]

found_versions = []


def scan(data, start, end, depth=0, hex_dump=False):
    offset = start
    indent = "  " * depth

    while offset + 8 <= end:
        chunk_id   = data[offset:offset+4]
        chunk_size = u32be(data, offset + 4)
        data_start = offset + 8
        data_end   = min(data_start + chunk_size, len(data))
        fcc        = safe_fourcc(chunk_id)

        print(f"{indent}[{offset:08x}] '{fcc}'  size={chunk_size}")

        if hex_dump and chunk_size > 0:
            preview_bytes = data[data_start:min(data_start+64, data_end)]
            print(f"{indent}         hex: {hex_preview(preview_bytes)}")

        # --- Try every interpretation of the chunk data ---
        if chunk_size >= 4:
            raw = data[data_start:data_start+8]

            # Print all plausible 16-bit and 32-bit readings
            interpretations = []
            if len(raw) >= 2:
                interpretations.append(f"u16be[0]={u16be(data, data_start)}")
                if len(raw) >= 4:
                    interpretations.append(f"u16be[1]={u16be(data, data_start+2)}")
            if len(raw) >= 4:
                interpretations.append(f"u32be={u32be(data, data_start)}")
                interpretations.append(f"u32be>>16={u32be(data, data_start)>>16}")
                interpretations.append(f"u32be&0xFFFF={u32be(data, data_start)&0xFFFF}")
            if len(raw) >= 4:
                interpretations.append(f"u32le={u32le(data, data_start)}")

            if chunk_id in VERSION_CHUNK_IDS or fcc in [safe_fourcc(v) for v in VERSION_CHUNK_IDS]:
                print(f"{indent}  *** CANDIDATE VERSION CHUNK ***")
                for interp in interpretations:
                    print(f"{indent}      {interp}")

                # Highlight any value in AE version range (2500–4000)
                for i in range(min(chunk_size, 16) - 1):
                    v = u16be(data, data_start + i)
                    if 2500 <= v <= 4000:
                        found_versions.append({
                            "chunk": fcc,
                            "file_offset": data_start + i,
                            "value": v,
                            "hex": hex(v),
                        })
                        print(f"{indent}  *** POSSIBLE VERSION @ offset {data_start+i:#010x}: {v} ({hex(v)}) ***")
            else:
                # Even for non-candidate chunks, flag any u16 in AE range
                for i in range(min(chunk_size, 32) - 1):
                    v = u16be(data, data_start + i)
                    if 2600 <= v <= 3700:
                        print(f"{indent}  ~ u16={v} ({hex(v)}) @ +{i} inside '{fcc}' (possible version?)")

        # Recurse into list/container chunks
        if chunk_id in LIST_CHUNKS and chunk_size >= 4:
            sub_form = data[data_start:data_start+4]
            print(f"{indent}  [form: '{safe_fourcc(sub_form)}']")
            scan(data, data_start + 4, data_end, depth + 1, hex_dump)

        # Advance past chunk (pad to even)
        advance = 8 + chunk_size
        if advance % 2:
            advance += 1
        offset += advance


def main():
    parser = argparse.ArgumentParser(description="AEP/FFX binary inspector")
    parser.add_argument("file", help=".aep or .ffx file to inspect")
    parser.add_argument("--hex-dump", action="store_true", help="Show hex preview of each chunk")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    data = path.read_bytes()
    print(f"File: {path.name}  ({len(data):,} bytes)")
    print(f"Magic: {data[:4]!r}  Form: {data[8:12]!r}")
    print()

    # Sanity check
    if data[:4] not in (b"RIFX", b"RIFF"):
        print("WARNING: File does not start with RIFX or RIFF magic!")
        print(f"First 16 bytes: {data[:16].hex()}")
        print()

    root_size = u32be(data, 4)
    print(f"Root chunk size: {root_size}  (file size: {len(data)})")
    print("=" * 70)
    print()

    scan(data, 12, min(12 + root_size, len(data)), depth=0, hex_dump=args.hex_dump)

    print()
    print("=" * 70)
    print("SUMMARY — candidate version values found:")
    if found_versions:
        for v in found_versions:
            print(f"  chunk='{v['chunk']}'  offset={v['file_offset']:#010x}  value={v['value']}  hex={v['hex']}")
    else:
        print("  None found in known AE version range (2500–4000).")
        print()
        print("  Try --hex-dump and look manually for bytes like:")
        print("    0DC0 (2024), 0D80 (2023), 0D40 (2022), 0D00 (2021)")
        print("    0CC0 (2020), 0C80 (CC2019), 0C40 (CC2018), 0C00 (CC2017)")


if __name__ == "__main__":
    main()
