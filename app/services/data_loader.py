import os
import pandas as pd
import pickle
import re
import glob
from app.config import Config
from app import DATA_STORE

# Pre-computed site index for instant lookups
SITE_INDEX = {}

def get_cache_path(file_path):
    os.makedirs(Config.CACHE_DIR, exist_ok=True)
    filename = os.path.basename(file_path)
    return os.path.join(Config.CACHE_DIR, f"{filename}.pkl")

def load_excel_file(file_path):
    cache_path = get_cache_path(file_path)
    if os.path.exists(cache_path):
        if os.environ.get('PORT') or os.path.getmtime(cache_path) > os.path.getmtime(file_path):
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
    print(f"  Parsing: {os.path.basename(file_path)}...")
    import gc
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        # Fill NaN and convert to string to save memory and avoid type issues
        df = df.fillna("-").astype(str)
        with open(cache_path, 'wb') as f:
            pickle.dump(df, f)
        gc.collect()
        return df
    except Exception as e:
        print(f"  ERROR loading {file_path}: {e}")
        return pd.DataFrame()

def _extract_site_code_from_cell(cell_name):
    if not cell_name or not isinstance(cell_name, str):
        return ""
    name = cell_name.strip().upper()
    match = re.match(r'^[345]?([A-Z])(\d{2}[A-Z]\d{3,4})', name)
    if match:
        return match.group(2)
    match = re.search(r'(\d{2}[A-Z]\d{3,4})', name)
    if match:
        return match.group(1)
    return ""

def _find_name_column(df):
    """Find the most likely column containing cell/site/NE names."""
    priority = ['cell name', 'ne name', 'nename', 'site name', 'bts name', 'nodeb name']
    for col in df.columns:
        if col.lower().strip() in priority:
            return col
    # Fallback: any column with 'name' in it
    for col in df.columns:
        if 'name' in col.lower():
            return col
    return None

def _build_site_index():
    global SITE_INDEX
    SITE_INDEX.clear()
    print("  Building site index across all datasets...")
    
    for key, df in DATA_STORE.items():
        if df.empty:
            continue
        name_col = _find_name_column(df)
        if not name_col:
            continue
        for idx, row in df.iterrows():
            site_code = _extract_site_code_from_cell(str(row.get(name_col, "")))
            if site_code and len(site_code) >= 6:
                if site_code not in SITE_INDEX:
                    SITE_INDEX[site_code] = {}
                if key not in SITE_INDEX[site_code]:
                    SITE_INDEX[site_code][key] = []
                SITE_INDEX[site_code][key].append(idx)
    
    print(f"  Site index built: {len(SITE_INDEX)} unique sites across {len(DATA_STORE)} datasets.")

def _scan_report_dir(dir_name, prefix):
    """Scan a Report directory and load all xlsx files with a meaningful key name."""
    base = Config.BASE_DIR
    report_dir = os.path.join(base, dir_name)
    if not os.path.isdir(report_dir):
        return
    
    for fpath in sorted(glob.glob(os.path.join(report_dir, "*.xlsx"))):
        fname = os.path.basename(fpath)
        # Create a clean dataset key: e.g. "4G_LTE_RRU_Report" from "LTE_RRU_Report_2025..._CONVERTED.xlsx"
        clean_name = re.sub(r'_\d{14}_CONVERTED', '', fname.replace('.xlsx', ''))
        key = f"{prefix}_{clean_name}"
        DATA_STORE[key] = load_excel_file(fpath)
        print(f"  {key}: {len(DATA_STORE[key])} rows")

def load_all_data():
    DATA_STORE.clear()
    base = Config.BASE_DIR
    
    # Core datasets
    core_files = {
        "2G": os.path.join(base, "2G.xlsx"),
        "3G": os.path.join(base, "3G.xlsx"),
        "4G": os.path.join(base, "4G.xlsx"),
        "5G": os.path.join(base, "5G.xlsx"),
        "Equipment": os.path.join(base, "RI HUawei 23-12-25.xlsx"),
        "Nominations": os.path.join(base, "cells nominations.xlsx"),
    }
    
    print("[DataLoader] === Loading Core Datasets ===")
    for key, path in core_files.items():
        if os.path.exists(path):
            DATA_STORE[key] = load_excel_file(path)
            print(f"  {key}: {len(DATA_STORE[key])} rows")
        else:
            print(f"  MISSING: {path}")
            DATA_STORE[key] = pd.DataFrame()
    
    # Extended report datasets (the 39 files)
    print("[DataLoader] === Loading Extended Reports ===")
    _scan_report_dir("Report_2G", "2G")
    _scan_report_dir("Report_3G", "3G")
    _scan_report_dir("Report_4G", "4G")
    _scan_report_dir("Report_5G", "5G")
    
    print(f"[DataLoader] Total datasets loaded: {len(DATA_STORE)}")
    _build_site_index()
    print("[DataLoader] === All data loaded successfully ===")

def get_dataframe(key):
    return DATA_STORE.get(key, pd.DataFrame())

def get_all_dataset_names():
    return sorted([k for k, v in DATA_STORE.items() if not v.empty])

def get_dataset_page(name, page=1, per_page=50, search=""):
    df = DATA_STORE.get(name, pd.DataFrame())
    if df.empty:
        return [], 0, []
    if search and len(search) >= 2:
        mask = df.astype(str).apply(
            lambda col: col.str.lower().str.contains(search.lower(), na=False, regex=False)
        ).any(axis=1)
        df = df[mask]
    total = len(df)
    start = (page - 1) * per_page
    end = start + per_page
    page_df = df.iloc[start:end].fillna("-")
    return page_df.to_dict('records'), total, df.columns.tolist()

def is_data_loaded():
    for df in DATA_STORE.values():
        if not df.empty:
            return True
    return False

def get_site_index():
    return SITE_INDEX

def get_all_site_codes():
    return sorted(SITE_INDEX.keys())
