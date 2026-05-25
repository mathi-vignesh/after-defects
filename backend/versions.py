# After Effects version registry
#
# GROUND TRUTH from real file analysis:
#   AE 22: head_data[1,3,4,5,6,7] = [0x5d, 0x09, 0x0b, 0x3b, 0x4e, 0x02]
#   AE 23: head_data[1,3,4,5,6,7] = [0x5e, 0x09, 0x0b, 0x3b, 0x4e, 0x02]
#   (bytes 3-7 are IDENTICAL between v22 and v23)
#
# For versions without real file data, secondary bytes are estimated from
# the AEPdowngrader.py open-source reference. Only byte[1] is guaranteed correct.
#
# Formula: head_data[1] = 0x5b + (app_major_version - 20)

# Signatures: [head1, head3, head4, head5, head6, head7]
# Confirmed from real files marked with (*)
_SIGS = {
    25: [0x60, 0x09, 0x0f, 0x0b, 0x06, 0x65],  # estimated
    24: [0x5f, 0x05, 0x0f, 0x02, 0x86, 0x34],  # from reference script
    23: [0x5e, 0x09, 0x0b, 0x3b, 0x4e, 0x02],  # (*) confirmed real file
    22: [0x5d, 0x09, 0x0b, 0x3b, 0x4e, 0x02],  # (*) confirmed real file
    18: [0x59, 0x09, 0x0b, 0x3b, 0x4e, 0x02],  # estimated (same pattern as 22/23)
    17: [0x58, 0x09, 0x0b, 0x3b, 0x4e, 0x02],  # estimated
    16: [0x57, 0x09, 0x0b, 0x3b, 0x4e, 0x02],  # estimated
    15: [0x56, 0x09, 0x0b, 0x3b, 0x4e, 0x02],  # estimated
    14: [0x55, 0x09, 0x0b, 0x3b, 0x4e, 0x02],  # estimated
    13: [0x54, 0x09, 0x0b, 0x3b, 0x4e, 0x02],  # estimated
    12: [0x53, 0x09, 0x0b, 0x3b, 0x4e, 0x02],  # estimated
    11: [0x52, 0x09, 0x0b, 0x3b, 0x4e, 0x02],  # estimated
    10: [0x51, 0x09, 0x0b, 0x3b, 0x4e, 0x02],  # estimated
}

AE_VERSIONS = [
    {"ver": 25, "short": "2025",    "name": "After Effects 2025",    "year": 2025, "app_ver": "25.x"},
    {"ver": 24, "short": "2024",    "name": "After Effects 2024",    "year": 2024, "app_ver": "24.x"},
    {"ver": 23, "short": "2023",    "name": "After Effects 2023",    "year": 2023, "app_ver": "23.x"},
    {"ver": 22, "short": "2022",    "name": "After Effects 2022",    "year": 2022, "app_ver": "22.x"},
    {"ver": 18, "short": "2021",    "name": "After Effects 2021",    "year": 2021, "app_ver": "18.x"},
    {"ver": 17, "short": "2020",    "name": "After Effects 2020",    "year": 2020, "app_ver": "17.x"},
    {"ver": 16, "short": "CC 2019", "name": "After Effects CC 2019", "year": 2019, "app_ver": "16.x"},
    {"ver": 15, "short": "CC 2018", "name": "After Effects CC 2018", "year": 2018, "app_ver": "15.x"},
    {"ver": 14, "short": "CC 2017", "name": "After Effects CC 2017", "year": 2017, "app_ver": "14.x"},
    {"ver": 13, "short": "CC 2014", "name": "After Effects CC 2014", "year": 2014, "app_ver": "13.x"},
    {"ver": 12, "short": "CC 12",   "name": "After Effects CC",      "year": 2013, "app_ver": "12.x"},
    {"ver": 11, "short": "CS6",     "name": "After Effects CS6",     "year": 2012, "app_ver": "11.x"},
    {"ver": 10, "short": "CS5",     "name": "After Effects CS5",     "year": 2010, "app_ver": "10.x"},
]

for _v in AE_VERSIONS:
    _v["byte"] = 0x5b + (_v["ver"] - 20)
    _v["hex"]  = f"0x{_v['byte']:02x}"
    _v["sig"]  = _SIGS[_v["ver"]]
    _v["sig_confirmed"] = _v["ver"] in (22, 23)

VERSION_BY_BYTE = {v["byte"]: v for v in AE_VERSIONS}
VERSION_BY_VER  = {v["ver"]:  v for v in AE_VERSIONS}

def get_version_by_byte(b: int):
    return VERSION_BY_BYTE.get(b)

def get_versions_below_byte(b: int):
    return sorted(
        [v for v in AE_VERSIONS if v["byte"] < b],
        key=lambda v: v["byte"],
        reverse=True
    )

def get_closest_version(b: int):
    if not AE_VERSIONS:
        return None
    return min(AE_VERSIONS, key=lambda v: abs(v["byte"] - b))

def byte_to_ver(b: int) -> int:
    return b - 0x5b + 20
