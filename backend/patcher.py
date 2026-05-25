"""
Patcher for After Effects RIFX files.

Patching strategy (from AEPdowngrader.py open-source reference + real file analysis):

  The version lives in head_data (content[32:52]).
  - head_data[1]  = version byte  (content[33])  — always changes
  - head_data[3]  = secondary byte — changes for larger version gaps
  - head_data[4]  = 0x0b (<=23) / 0x0f (>=24)
  - head_data[5]  = version-specific value
  - head_data[6]  = version-specific value
  - head_data[7]  = version-specific value

  For adjacent version steps (e.g. 23→22), only head_data[1] changes.
  For larger jumps, we patch all 6 bytes to match the target signature.
"""

from parser import parse_aep, VersionInfo, RIFXParseError, _find_head_chunk
from versions import get_version_by_byte, get_versions_below_byte


class PatchError(Exception):
    pass


# Offsets within head_data (relative to head chunk data start = head_offset + 8)
# These correspond to content[32:52] when head chunk is at standard position 0x18
SIG_OFFSETS = [1, 3, 4, 5, 6, 7]   # indices into head_data


def patch_aep(data: bytes, target_byte: int) -> tuple[bytes, dict]:
    try:
        src: VersionInfo = parse_aep(data)
    except RIFXParseError as e:
        raise PatchError(f"Parse failed: {e}")

    if target_byte >= src.version_byte:
        raise PatchError("Target version must be lower than the source version.")

    target = get_version_by_byte(target_byte)
    if target is None:
        raise PatchError(f"Unknown target version byte: 0x{target_byte:02x}")

    # Find head chunk data start
    head_chunk_offset = _find_head_chunk(data)
    if head_chunk_offset is None:
        raise PatchError("Could not locate 'head' chunk.")
    head_data_start = head_chunk_offset + 8  # skip 4-byte id + 4-byte size

    # Build target signature
    target_sig = target["sig"]   # [head1, head3, head4, head5, head6, head7]

    patched = bytearray(data)
    modifications = 0

    for i, rel_offset in enumerate(SIG_OFFSETS):
        file_offset  = head_data_start + rel_offset
        current_val  = patched[file_offset]
        target_val   = target_sig[i]

        if current_val != target_val:
            patched[file_offset] = target_val
            modifications += 1

    info = {
        "source_version_byte":  src.version_byte,
        "source_version_name":  src.version_name,
        "target_version_byte":  target_byte,
        "target_version_name":  target["name"],
        "target_version_short": target["short"],
        "file_type":            src.file_type,
        "modifications":        modifications,
        "warnings":             _generate_warnings(src.version_byte, target_byte),
    }

    return bytes(patched), info


def _generate_warnings(src_byte: int, tgt_byte: int) -> list[str]:
    warnings = [
        "Downgraded projects may fail to open if they use effects, "
        "expressions, or features not available in the target version."
    ]
    gap = src_byte - tgt_byte
    if gap >= 4:
        warnings.append("Large version gap detected. Test thoroughly before using in production.")
    if tgt_byte <= 0x52:  # CS6 or older
        warnings.append("Target is CS6 or older. Modern expressions and 3D features will not be available.")
    return warnings


def get_downgrade_options(data: bytes) -> dict:
    try:
        info = parse_aep(data)
    except RIFXParseError as e:
        raise PatchError(str(e))

    targets = get_versions_below_byte(info.version_byte)

    return {
        "source": {
            "version_byte":   info.version_byte,
            "version_hex":    info.version_hex,
            "version_name":   info.version_name,
            "version_short":  info.version_short,
            "version_year":   info.version_year,
            "app_ver":        info.app_ver,
            "is_exact_match": info.is_exact_match,
            "file_type":      info.file_type,
        },
        "targets": targets,
    }
