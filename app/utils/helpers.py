import pandas as pd
from functools import wraps
from flask import session, jsonify

def safe_str(val):
    if pd.isna(val) or val is None or val == "" or str(val).strip() == "nan" or str(val).strip() == "<NA>":
        return "-"
    return str(val).strip()

def safe_float(val, precision=2):
    if pd.isna(val) or val is None or val == "" or str(val).strip() == "nan":
        return "-"
    try:
        return round(float(val), precision)
    except:
        return "-"

def safe_int(val):
    if pd.isna(val) or val is None or val == "" or str(val).strip() == "nan":
        return "-"
    try:
        return int(float(val))
    except:
        return "-"
