"""
Djezzy BSS — Site Utilities
Sector extraction based on the cells nominations matrix.

NOMINATIONS MATRIX SUMMARY (verified from cells nominations.xlsx):
─────────────────────────────────────────────────────────────────
2G GSM900:   _1→S1, _2→S2, _3→S3, _7→S4
2G DCS1800:  _4→S1, _5→S2, _6→S3

3G (sector = last digit of suffix):
   U900  (UARFCN ~2986-3007): _21→S1, _22→S2, _23→S3, _24→S4, _26→S1(F2)...
   U2100 (UARFCN ~10763):     _1→S1, _2→S2, _3→S3, _4→S4, _31→S1(F2), _32→S2(F2)...

4G (band from 'Frequency band' column):
   L1800  (B3):  _1→S1, _2→S2, _3→S3, _41→S1, _42→S2, _43→S3 (F2), MIMO: _11X→S1, _12X→S2, _13X→S3, _17X→S4
   L2100  (B1):  _4→S1, _5→S2, _6→S3, _91→S1, _92→S2, _93→S3 (F2), MIMO: _14X→S1, _15X→S2, _16X→S3, _18X→S4
   L900   (B8):  _97→S1, _98→S2, _99→S3, _100→S4 (NA cells)
   TDD2300(B40): _21X→S1, _22X→S2, _23X→S3, _24X→S4

5G NR N78:
   F1 (70M):  _3601→S1, _3602→S2, _3603→S3, _3604→S4
   F2 (100M): _3701→S1, _3702→S2, _3703→S3, _3704→S4
"""
import re

# ─── UARFCN Ranges ───
U900_RANGE = range(2900, 3100)   # DL UARFCNs for U900
U2100_RANGE = range(10600, 10900)  # DL UARFCNs for U2100

# ─── Band Labels ───
LTE_BAND_MAP = {"1": "L2100", "3": "L1800", "8": "L900", "40": "TDD2300"}
NR_BAND_MAP = {"n78": "NR_N78", "N78": "NR_N78", "78": "NR_N78", "n77": "NR_N77", "N77": "NR_N77"}

# ─── Site Code Extraction ───
def extract_site_code(cell_name):
    """Extract base site code from any Djezzy cell name format.
    Handles: A16X174_1, 3A16X174_21, 4A06X020_210, 5A16M995_3601, 3C18X016_21
    """
    if not cell_name or not isinstance(cell_name, str):
        return ""
    name = cell_name.strip().upper()
    # Remove _NA suffix if present
    name = re.sub(r'_NA$', '', name)
    
    # Pattern: optional tech prefix (3,4,5) + letter(A-Z) + site_code(2dig+letter+3-4dig) + _suffix
    match = re.match(r'^[345]?([A-Z])(\d{2}[A-Z]\d{3,4})', name)
    if match:
        return match.group(2)
    # Fallback
    match = re.search(r'(\d{2}[A-Z]\d{3,4})', name)
    if match:
        return match.group(1)
    return ""

def get_cell_suffix(cell_name):
    """Extract the numeric suffix after the last underscore.
    A16X174_1 → '1', 4A06X020_210 → '210', 4A06X020_97_NA → '97'
    """
    if not cell_name or not isinstance(cell_name, str):
        return ""
    name = cell_name.strip().upper()
    # Remove _NA suffix before extracting
    name = re.sub(r'_NA$', '', name)
    parts = name.split('_')
    if len(parts) >= 2:
        return parts[-1]
    return ""

# ─── 2G Band & Sector ───
def classify_2g(freq_band_str, suffix):
    """Returns (band_label, sector_number)"""
    band = freq_band_str.strip().upper() if freq_band_str else ""
    
    if "DCS" in band or "1800" in band:
        band_label = "DCS1800"
    else:
        band_label = "GSM900"
    
    # 2G sector mapping from nominations
    suffix_map_gsm = {'1': 1, '2': 2, '3': 3, '7': 4}
    suffix_map_dcs = {'4': 1, '5': 2, '6': 3}
    
    s = suffix.strip()
    if band_label == "DCS1800":
        return band_label, suffix_map_dcs.get(s, int(s) if s.isdigit() else 0)
    else:
        return band_label, suffix_map_gsm.get(s, int(s) if s.isdigit() else 0)

# ─── 3G Band & Sector ───
def classify_3g(uarfcn_str, suffix):
    """Returns (band_label, sector_number)"""
    try:
        uarfcn = int(float(uarfcn_str))
    except:
        uarfcn = 0
    
    if uarfcn in U900_RANGE:
        band_label = "U900"
    else:
        band_label = "U2100"
    
    # 3G: sector = last digit of suffix
    s = suffix.strip()
    if s and s[-1].isdigit():
        sector = int(s[-1])
        if sector == 0:
            # _10, _20, _30 etc. are special carriers, treat as sector based on tens digit
            if len(s) >= 2 and s[-2].isdigit():
                sector = int(s[-2])
            else:
                sector = 1
        return band_label, sector
    return band_label, 0

# ─── 4G Band & Sector ───
def classify_4g(freq_band_str, suffix):
    """Returns (band_label, sector_number)"""
    band_num = freq_band_str.strip() if freq_band_str else ""
    band_label = LTE_BAND_MAP.get(band_num, f"L_B{band_num}" if band_num else "L_Unknown")
    
    s = suffix.strip()
    if not s or not s.isdigit():
        return band_label, 0
    
    sn = int(s)
    
    if band_label == "TDD2300":
        # TDD: _21X→S1, _22X→S2, _23X→S3, _24X→S4
        if 210 <= sn <= 219: return band_label, 1
        if 220 <= sn <= 229: return band_label, 2
        if 230 <= sn <= 239: return band_label, 3
        if 240 <= sn <= 249: return band_label, 4
        return band_label, 0
    
    if band_label == "L900":
        # L900: _97→S1, _98→S2, _99→S3, _100→S4
        if sn == 97: return band_label, 1
        if sn == 98: return band_label, 2
        if sn == 99: return band_label, 3
        if sn == 100: return band_label, 4
        return band_label, 0
    
    if band_label == "L1800":
        # Simple: _1→S1, _2→S2, _3→S3
        if sn in (1,): return band_label, 1
        if sn in (2,): return band_label, 2
        if sn in (3,): return band_label, 3
        # F2: _41→S1, _42→S2, _43→S3
        if sn in (41,): return band_label, 1
        if sn in (42,): return band_label, 2
        if sn in (43,): return band_label, 3
        # MIMO: _11X→S1, _12X→S2, _13X→S3, _17X→S4
        if 110 <= sn <= 119: return band_label, 1
        if 120 <= sn <= 129: return band_label, 2
        if 130 <= sn <= 139: return band_label, 3
        if 170 <= sn <= 179: return band_label, 4
        return band_label, 0
    
    if band_label == "L2100":
        # Simple: _4→S1, _5→S2, _6→S3
        if sn in (4,): return band_label, 1
        if sn in (5,): return band_label, 2
        if sn in (6,): return band_label, 3
        # F2: _91→S1, _92→S2, _93→S3
        if sn in (91,): return band_label, 1
        if sn in (92,): return band_label, 2
        if sn in (93,): return band_label, 3
        # MIMO: _14X→S1, _15X→S2, _16X→S3, _18X→S4
        if 140 <= sn <= 149: return band_label, 1
        if 150 <= sn <= 159: return band_label, 2
        if 160 <= sn <= 169: return band_label, 3
        if 180 <= sn <= 189: return band_label, 4
        return band_label, 0
    
    # Unknown band — try last digit
    if s[-1].isdigit():
        return band_label, int(s[-1]) if int(s[-1]) > 0 else 1
    return band_label, 0

# ─── 5G Band & Sector ───
def classify_5g(freq_band_str, suffix):
    """Returns (band_label, sector_number)"""
    band = freq_band_str.strip().upper() if freq_band_str else "N78"
    if "77" in band:
        band_label = "NR_N77"
    else:
        band_label = "NR_N78"
    
    s = suffix.strip()
    if not s or not s.isdigit():
        return band_label, 0
    
    sn = int(s)
    # NR: _36X1→S1, _36X2→S2, _36X3→S3, _36X4→S4 (F1)
    #     _37X1→S1, _37X2→S2, _37X3→S3, _37X4→S4 (F2)
    # Sector = last digit
    sector = sn % 10
    if sector == 0:
        sector = 1  # fallback
    if sector > 6:
        sector = 1  # fallback for unusual suffixes
    return band_label, sector

# ─── Master Classification ───
BAND_ORDER = ["GSM900", "DCS1800", "U900", "U2100", "L900", "L1800", "L2100", "TDD2300", "NR_N78", "NR_N77"]

BAND_COLORS = {
    "GSM900":  "#3B82F6",
    "DCS1800": "#60A5FA",
    "U900":    "#7C3AED",
    "U2100":   "#A78BFA",
    "L900":    "#F97316",
    "L1800":   "#F59E0B",
    "L2100":   "#FBBF24",
    "TDD2300": "#EF4444",
    "NR_N78":  "#10B981",
    "NR_N77":  "#06B6D4",
}

TECH_FOR_BAND = {
    "GSM900": "2G", "DCS1800": "2G",
    "U900": "3G", "U2100": "3G",
    "L900": "4G", "L1800": "4G", "L2100": "4G", "TDD2300": "4G",
    "NR_N78": "5G", "NR_N77": "5G",
}
