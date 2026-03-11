"""
Djezzy BSS Analytics Engine
Computes per-band per-sector configurations: x/x/x/x for each band.
"""
from collections import defaultdict
import pandas as pd
from app.services.data_loader import get_dataframe, get_site_index, get_all_site_codes, DATA_STORE
from app.utils.site_utils import (
    extract_site_code, get_cell_suffix,
    classify_2g, classify_3g, classify_4g, classify_5g,
    BAND_ORDER, BAND_COLORS, TECH_FOR_BAND
)

MAX_SECTORS = 4  # Most Djezzy sites have up to 4 sectors


class AnalyticsService:

    @staticmethod
    def _compute_site_config(site_code):
        """Compute per-band per-sector cell count.
        Returns dict: {band_label: [S1_count, S2_count, S3_count, S4_count]}
        """
        site_index = get_site_index()
        site_data = site_index.get(site_code.upper(), {})
        if not site_data:
            return {}

        band_sectors = defaultdict(lambda: defaultdict(int))  # {band: {sector: count}}

        # --- 2G ---
        df2g = get_dataframe("2G")
        if not df2g.empty and "2G" in site_data:
            for idx in site_data["2G"]:
                if idx >= len(df2g):
                    continue
                row = df2g.iloc[idx]
                cell_name = str(row.get("Cell Name", ""))
                freq_band = str(row.get("Freq. Band", ""))
                suffix = get_cell_suffix(cell_name)
                band_label, sector = classify_2g(freq_band, suffix)
                if sector > 0:
                    band_sectors[band_label][sector] += 1

        # --- 3G ---
        df3g = get_dataframe("3G")
        if not df3g.empty and "3G" in site_data:
            for idx in site_data["3G"]:
                if idx >= len(df3g):
                    continue
                row = df3g.iloc[idx]
                cell_name = str(row.get("Cell Name", ""))
                uarfcn = str(row.get("Downlink UARFCN", ""))
                suffix = get_cell_suffix(cell_name)
                band_label, sector = classify_3g(uarfcn, suffix)
                if sector > 0:
                    band_sectors[band_label][sector] += 1

        # --- 4G ---
        df4g = get_dataframe("4G")
        if not df4g.empty and "4G" in site_data:
            for idx in site_data["4G"]:
                if idx >= len(df4g):
                    continue
                row = df4g.iloc[idx]
                cell_name = str(row.get("Cell Name", ""))
                freq_band = str(row.get("Frequency band", ""))
                suffix = get_cell_suffix(cell_name)
                band_label, sector = classify_4g(freq_band, suffix)
                if sector > 0:
                    band_sectors[band_label][sector] += 1

        # --- 5G ---
        df5g = get_dataframe("5G")
        if not df5g.empty and "5G" in site_data:
            for idx in site_data["5G"]:
                if idx >= len(df5g):
                    continue
                row = df5g.iloc[idx]
                cell_name = str(row.get("Cell Name", ""))
                freq_band = str(row.get("Frequency Band", ""))
                suffix = get_cell_suffix(cell_name)
                band_label, sector = classify_5g(freq_band, suffix)
                if sector > 0:
                    band_sectors[band_label][sector] += 1

        # Build result: {band: [S1, S2, S3, S4]}
        result = {}
        for band in BAND_ORDER:
            if band in band_sectors:
                sectors = band_sectors[band]
                result[band] = [sectors.get(s, 0) for s in range(1, MAX_SECTORS + 1)]
        return result

    @staticmethod
    def get_config_display(site_code):
        """Get formatted config display for a site."""
        config = AnalyticsService._compute_site_config(site_code)
        bands = []
        for band in BAND_ORDER:
            if band in config:
                sector_str = "/".join(str(x) for x in config[band])
                bands.append({
                    "band": band,
                    "tech": TECH_FOR_BAND.get(band, "?"),
                    "sectors": config[band],
                    "config_str": sector_str,
                    "color": BAND_COLORS.get(band, "#888"),
                    "total_cells": sum(config[band]),
                })
        return bands

    @staticmethod
    def get_site_profile(site_code):
        """Full site profile with per-band config, all parameters, equipment, and extended data."""
        import re
        site_code = site_code.strip().upper()
        # Strip technology prefix if present (A, 3A, 4A, 5A, 3C, etc.)
        m = re.match(r'^[345]?[A-Z](\d{2}[A-Z]\d{3,4})', site_code)
        if m:
            site_code = m.group(1)
        site_index = get_site_index()
        site_data = site_index.get(site_code, {})

        config_bands = AnalyticsService.get_config_display(site_code)

        # Collect all cells per technology with ALL parameters
        technologies = {}
        for tech_key in ["2G", "3G", "4G", "5G"]:
            df = get_dataframe(tech_key)
            if df.empty or tech_key not in site_data:
                continue
            cells = []
            for idx in site_data[tech_key]:
                if idx >= len(df):
                    continue
                row = df.iloc[idx]
                cell_dict = {}
                for col in df.columns:
                    val = row.get(col)
                    cell_dict[col] = str(val) if pd.notna(val) else "-"

                # Add computed band + sector
                cell_name = str(row.get("Cell Name", ""))
                suffix = get_cell_suffix(cell_name)
                if tech_key == "2G":
                    b, s = classify_2g(str(row.get("Freq. Band", "")), suffix)
                elif tech_key == "3G":
                    b, s = classify_3g(str(row.get("Downlink UARFCN", "")), suffix)
                elif tech_key == "4G":
                    b, s = classify_4g(str(row.get("Frequency band", "")), suffix)
                else:
                    b, s = classify_5g(str(row.get("Frequency Band", "")), suffix)
                cell_dict["_band"] = b
                cell_dict["_sector"] = s
                cell_dict["_band_color"] = BAND_COLORS.get(b, "#888")
                cells.append(cell_dict)

            if cells:
                # Sort by sector then band
                cells.sort(key=lambda c: (c.get("_sector", 0), c.get("_band", "")))
                technologies[tech_key] = cells

        # Equipment
        equipment = []
        eq_df = get_dataframe("Equipment")
        if not eq_df.empty and "Equipment" in site_data:
            for idx in site_data["Equipment"]:
                if idx >= len(eq_df):
                    continue
                row = eq_df.iloc[idx]
                eq_dict = {}
                for col in eq_df.columns:
                    val = row.get(col)
                    eq_dict[col] = str(val) if pd.notna(val) else "-"
                equipment.append(eq_dict)

        # Extended data from Report files
        extended = {}
        for key in DATA_STORE:
            if key in ["2G", "3G", "4G", "5G", "Equipment", "Nominations"]:
                continue
            if key in site_data:
                df = DATA_STORE[key]
                rows = []
                for idx in site_data[key]:
                    if idx >= len(df):
                        continue
                    row = df.iloc[idx]
                    rd = {}
                    for col in df.columns:
                        val = row.get(col)
                        rd[col] = str(val) if pd.notna(val) else "-"
                    rows.append(rd)
                if rows:
                    extended[key] = rows

        return {
            "site_code": site_code,
            "config_bands": config_bands,
            "technologies": technologies,
            "equipment": equipment,
            "extended": extended,
            "band_order": BAND_ORDER,
            "band_colors": BAND_COLORS,
        }

    @staticmethod
    def get_sites_list(page=1, per_page=50, search=""):
        """Paginated list of all sites with their per-band configs."""
        all_codes = get_all_site_codes()
        if search:
            import re
            search_upper = search.strip().upper()
            # Strip technology prefix if present (A, 3A, 4A, 5A, 3C, etc.)
            m = re.match(r'^[345]?[A-Z](\d{2}[A-Z]\d{3,4})', search_upper)
            if m:
                search_upper = m.group(1)
            all_codes = [c for c in all_codes if search_upper in c]

        total = len(all_codes)
        start = (page - 1) * per_page
        end = start + per_page
        page_codes = all_codes[start:end]

        sites = []
        for code in page_codes:
            config_bands = AnalyticsService.get_config_display(code)
            sites.append({
                "site_code": code,
                "config_bands": config_bands,
            })
        return sites, total

    @staticmethod
    def search_global(query, limit=50):
        """Search across all datasets for any parameter value."""
        if not query or len(query) < 2:
            return []
        q = query.lower()
        results = []

        for key, df in DATA_STORE.items():
            if df.empty or key == "Nominations":
                continue
            mask = df.astype(str).apply(
                lambda col: col.str.lower().str.contains(q, na=False, regex=False)
            ).any(axis=1)
            matched = df[mask].head(limit - len(results))
            for _, row in matched.iterrows():
                rd = {}
                for col in df.columns:
                    val = row.get(col)
                    rd[col] = str(val) if pd.notna(val) else "-"
                results.append({"source": key, "data": rd})
            if len(results) >= limit:
                break
        return results

    @staticmethod
    def search_by_parameter(param_name, param_value, limit=100):
        """Search for sites by a specific parameter name and value."""
        results = []
        pn = param_name.lower()
        pv = param_value.lower()

        for key, df in DATA_STORE.items():
            if df.empty or key == "Nominations":
                continue
            # Find columns matching the parameter name
            matched_cols = [c for c in df.columns if pn in c.lower()]
            if not matched_cols:
                continue
            for col in matched_cols:
                mask = df[col].astype(str).str.lower().str.strip() == pv
                matches = df[mask].head(limit - len(results))
                for _, row in matches.iterrows():
                    rd = {"_source": key, "_matched_column": col}
                    for c2 in df.columns:
                        val = row.get(c2)
                        rd[c2] = str(val) if pd.notna(val) else "-"
                    results.append(rd)
                if len(results) >= limit:
                    break
            if len(results) >= limit:
                break
        return results

    @staticmethod
    def get_dashboard_stats():
        """Rich dashboard statistics from all datasets."""
        stats = {
            "datasets": {},
            "total_sites": len(get_all_site_codes()),
        }

        # Row counts per dataset
        for key, df in DATA_STORE.items():
            if not df.empty:
                stats["datasets"][key] = len(df)

        # Technology cell counts
        tech_counts = {"2G": 0, "3G": 0, "4G": 0, "5G": 0}
        for tech in tech_counts:
            df = get_dataframe(tech)
            if not df.empty:
                tech_counts[tech] = len(df)
        stats["tech_counts"] = tech_counts

        # Band distribution from 4G
        df4g = get_dataframe("4G")
        band_dist = {}
        if not df4g.empty and "Frequency band" in df4g.columns:
            for val, label in [("3", "L1800"), ("1", "L2100"), ("8", "L900"), ("40", "TDD2300")]:
                count = len(df4g[df4g["Frequency band"].astype(str) == val])
                if count > 0:
                    band_dist[label] = count
        stats["band_distribution_4g"] = band_dist

        # 2G band distribution
        df2g = get_dataframe("2G")
        band_dist_2g = {}
        if not df2g.empty and "Freq. Band" in df2g.columns:
            for val in df2g["Freq. Band"].dropna().unique():
                band_dist_2g[str(val)] = len(df2g[df2g["Freq. Band"] == val])
        stats["band_distribution_2g"] = band_dist_2g

        # 3G UARFCN distribution
        df3g = get_dataframe("3G")
        band_dist_3g = {"U900": 0, "U2100": 0}
        if not df3g.empty and "Downlink UARFCN" in df3g.columns:
            for _, row in df3g.iterrows():
                try:
                    u = int(float(row.get("Downlink UARFCN", 0)))
                    if 2900 <= u <= 3100:
                        band_dist_3g["U900"] += 1
                    else:
                        band_dist_3g["U2100"] += 1
                except:
                    pass
        stats["band_distribution_3g"] = band_dist_3g

        # Equipment type distribution
        eq_df = get_dataframe("Equipment")
        eq_types = {}
        if not eq_df.empty and "EquipeType" in eq_df.columns:
            for val in eq_df["EquipeType"].dropna().unique():
                eq_types[str(val)] = len(eq_df[eq_df["EquipeType"] == val])
        stats["equipment_types"] = eq_types

        # Site count by wilaya (first 2 digits of site code)
        codes = get_all_site_codes()
        wilaya_dist = defaultdict(int)
        for code in codes:
            if len(code) >= 2:
                wilaya_dist[code[:2]] += 1
        stats["sites_by_wilaya"] = dict(sorted(wilaya_dist.items()))

        # Available parameter names (searchable columns)
        all_params = set()
        for key in ["2G", "3G", "4G", "5G"]:
            df = get_dataframe(key)
            if not df.empty:
                all_params.update(df.columns.tolist())
        stats["searchable_params"] = sorted(all_params)

        # ─── Expert Dashboard Stats ───
        # BTS Platform distribution
        platform_dist = defaultdict(int)
        for key in ["4G_LTE_Site_Report", "5G_NR_Site_Report"]:
            df = DATA_STORE.get(key, pd.DataFrame())
            if df.empty:
                continue
            ver_col = None
            for c in df.columns:
                if 'version' in c.lower():
                    ver_col = c
                    break
            if ver_col:
                for val in df[ver_col].dropna():
                    v = str(val)
                    if 'BTS5900' in v:
                        platform_dist["BTS5900"] += 1
                    elif 'BTS3900' in v:
                        platform_dist["BTS3900"] += 1
                    elif 'BTS3910' in v:
                        platform_dist["BTS3910"] += 1
                    else:
                        platform_dist["Other"] += 1
        stats["platform_distribution"] = dict(platform_dist)

        # RRU Type distribution
        rru_types = defaultdict(int)
        for key in ["4G_LTE_RRU_Report", "5G_NR_RRU_Report"]:
            df = DATA_STORE.get(key, pd.DataFrame())
            if df.empty or "RRU Name" not in df.columns:
                continue
            for val in df["RRU Name"].dropna():
                # Extract base model (e.g. "AAU5356 S1" → "AAU5356")
                name = str(val).split()[0] if str(val).strip() else "Unknown"
                rru_types[name] += 1
        stats["rru_type_distribution"] = dict(sorted(rru_types.items(), key=lambda x: -x[1])[:15])

        # RRU Working Mode distribution
        wm_dist = defaultdict(int)
        for key in ["4G_LTE_RRU_Report", "5G_NR_RRU_Report"]:
            df = DATA_STORE.get(key, pd.DataFrame())
            if df.empty or "RF Unit Working Mode" not in df.columns:
                continue
            for val in df["RF Unit Working Mode"].dropna():
                wm_dist[str(val)] += 1
        stats["rru_working_mode_distribution"] = dict(wm_dist)

        return stats

    # ═══════════════════════════════════════════
    #  EXPERT DATA — per-site deep analysis
    # ═══════════════════════════════════════════
    @staticmethod
    def _extract_site_from_ne(ne_name):
        """Extract site code from NE Name like 'MBTS_A16X677_Acc' → '16X677'."""
        import re
        if not ne_name:
            return ""
        m = re.search(r'[345]?[A-Z]?(\d{2}[A-Z]\d{3,4})', str(ne_name).upper())
        return m.group(1) if m else ""

    @staticmethod
    def get_expert_data(site_code):
        """Get expert-level analysis data for a site from extended reports."""
        import re
        site_code = site_code.strip().upper()
        m = re.match(r'^[345]?[A-Z](\d{2}[A-Z]\d{3,4})', site_code)
        if m:
            site_code = m.group(1)

        result = {
            "site_code": site_code,
            "nsa_anchoring": [],
            "x2_neighbors": [],
            "cpri_health": [],
            "rru_inventory": [],
            "hardware_versions": [],
            "network_kpis": [],
        }

        # ─── 1. NSA Anchoring (4G ↔ 5G) ───
        for key in ["4G_LTE_NSA_Report", "5G_NR_NSA_Report"]:
            df = DATA_STORE.get(key, pd.DataFrame())
            if df.empty:
                continue
            # Search by Local NE Name containing the site code
            mask = pd.Series([False] * len(df), index=df.index)
            for col in ["Local NE Name", "Local Cell Name"]:
                if col in df.columns:
                    mask = mask | df[col].astype(str).str.upper().str.contains(site_code, na=False, regex=False)
            matched = df[mask]
            for _, row in matched.head(100).iterrows():
                entry = {
                    "source": "4G→5G" if "LTE" in key else "5G→4G",
                    "local_cell": str(row.get("Local Cell Name", "-")),
                    "peer_cell": str(row.get("Peer Cell Name", "-")),
                    "local_type": str(row.get("Local NE Type", "-")),
                    "peer_type": str(row.get("Peer NE Type", "-")),
                    "x2_status": str(row.get("X2 Interface Status", "-")),
                }
                result["nsa_anchoring"].append(entry)

        # ─── 2. X2 Neighbor Topology ───
        for key in ["4G_LTE_X2_Interface_Report", "5G_NR_X2_Interface_Report"]:
            df = DATA_STORE.get(key, pd.DataFrame())
            if df.empty or "Local NE Name" not in df.columns:
                continue
            mask = df["Local NE Name"].astype(str).str.upper().str.contains(site_code, na=False, regex=False)
            matched = df[mask]
            for _, row in matched.head(50).iterrows():
                entry = {
                    "tech": "4G" if "LTE" in key else "5G",
                    "peer_name": str(row.get("Peer NE Name", "-")),
                    "peer_site": AnalyticsService._extract_site_from_ne(row.get("Peer NE Name", "")),
                    "local_x2_status": str(row.get("Local X2 Interface Status", "-")),
                    "peer_x2_status": str(row.get("Peer X2 Interface Status", "-")),
                    "sctp_status": str(row.get("Local SCTP Link Status", row.get("SCTP Link Status", "-"))),
                    "local_ip": str(row.get("Local IP Address of Local SCTP", "-")),
                    "peer_ip": str(row.get("Peer IP Address of Local SCTP", "-")),
                }
                result["x2_neighbors"].append(entry)

        # ─── 3. CPRI/Fronthaul Health ───
        for key in ["3G_UMTS_CPRI_Line_Rate_Report", "4G_LTE_CPRI_Line_Rate_Report", "5G_NR_CPRI_Line_Rate_Report"]:
            df = DATA_STORE.get(key, pd.DataFrame())
            if df.empty or "NE Name" not in df.columns:
                continue
            mask = df["NE Name"].astype(str).str.upper().str.contains(site_code, na=False, regex=False)
            matched = df[mask]
            for _, row in matched.head(30).iterrows():
                try:
                    line_rate = float(row.get("CPRI Line Rate(Mbit/s)", 0))
                    remaining = float(row.get("Remaining Bandwidth(Mbit/s)", 0))
                    allocated = float(row.get("Allocated CPRI Bandwidth by Local(Mbit/s)", 0))
                    utilization = round((allocated / line_rate * 100), 1) if line_rate > 0 else 0
                except (ValueError, TypeError):
                    line_rate = remaining = allocated = utilization = 0

                entry = {
                    "tech": "3G" if "UMTS" in key else ("4G" if "LTE" in key else "5G"),
                    "port": str(row.get("CPRI Port No.", "-")),
                    "port_type": str(row.get("Port Type", "-")),
                    "line_rate_mbps": line_rate,
                    "allocated_mbps": allocated,
                    "remaining_mbps": remaining,
                    "utilization_pct": utilization,
                    "rate_consistency": str(row.get("Rate Consistency", "-")),
                    "mux_type": str(row.get("CPRI Port Mux Type", "-")),
                }
                result["cpri_health"].append(entry)

        # ─── 4. RRU Inventory & Fiber Distance ───
        for key in ["4G_LTE_RRU_Report", "5G_NR_RRU_Report"]:
            df = DATA_STORE.get(key, pd.DataFrame())
            if df.empty:
                continue
            ne_col = "Base Station Name" if "Base Station Name" in df.columns else "NE Name"
            if ne_col not in df.columns:
                continue
            mask = df[ne_col].astype(str).str.upper().str.contains(site_code, na=False, regex=False)
            matched = df[mask]
            for _, row in matched.iterrows():
                entry = {
                    "tech": "4G" if "LTE" in key else "5G",
                    "rru_name": str(row.get("RRU Name", "-")),
                    "rru_type": str(row.get("RRU Type", "-")),
                    "working_mode": str(row.get("RF Unit Working Mode", "-")),
                    "availability": str(row.get("Availability Status", "-")),
                    "cell_name": str(row.get("Cell Name", "-")),
                    "pci": str(row.get("Physical Cell ID", "-")),
                }
                result["rru_inventory"].append(entry)

        # Add fiber distances
        for key in ["4G_LTE_RF-BBU_Distance_Report", "5G_NR_RF-BBU_Distance_Report"]:
            df = DATA_STORE.get(key, pd.DataFrame())
            if df.empty or "Base Station Name" not in df.columns:
                continue
            mask = df["Base Station Name"].astype(str).str.upper().str.contains(site_code, na=False, regex=False)
            matched = df[mask]
            for _, row in matched.iterrows():
                rru_name = str(row.get("RRU Name", "-"))
                fiber_len = str(row.get("Length of Fiber Optic Cable Between BBU and RRU (m)", "-"))
                # Update matching RRU entry
                for rru in result["rru_inventory"]:
                    if rru["rru_name"] == rru_name:
                        rru["fiber_length_m"] = fiber_len
                        break
                else:
                    result["rru_inventory"].append({
                        "tech": "4G" if "LTE" in key else "5G",
                        "rru_name": rru_name,
                        "rru_type": "-",
                        "working_mode": str(row.get("RRU Work Mode", "-")),
                        "availability": "-",
                        "cell_name": "-",
                        "pci": "-",
                        "fiber_length_m": fiber_len,
                    })

        # ─── 5. Hardware & Software Versions ───
        hw_map = {
            "2G_GSM_Site_Report": ("BSC Name", "NodeB Version", "2G"),
            "3G_UMTS_Site_Report": ("NodeB Name", "NodeB Version", "3G"),
            "4G_LTE_Site_Report": ("LTE NE Name", "LTE NE Version", "4G"),
            "5G_NR_Site_Report": ("NR NE Name", "NR NE Version", "5G"),
        }
        for key, (ne_col, ver_col, tech) in hw_map.items():
            df = DATA_STORE.get(key, pd.DataFrame())
            if df.empty or ne_col not in df.columns:
                continue
            mask = df[ne_col].astype(str).str.upper().str.contains(site_code, na=False, regex=False)
            matched = df[mask]
            for _, row in matched.head(5).iterrows():
                version = str(row.get(ver_col, "-")) if ver_col in df.columns else "-"
                platform = "BTS5900" if "BTS5900" in version else ("BTS3900" if "BTS3900" in version else "Unknown")
                entry = {
                    "tech": tech,
                    "ne_name": str(row.get(ne_col, "-")),
                    "version": version,
                    "platform": platform,
                }
                # Add extra fields per tech
                if tech == "3G" and "TnlBearer Type" in df.columns:
                    entry["transport"] = str(row.get("TnlBearer Type", "-"))
                result["hardware_versions"].append(entry)

        # ─── 6. S1 Interface (MME connectivity) ───
        s1_data = []
        df_s1 = DATA_STORE.get("4G_LTE_S1_Interface_Report", pd.DataFrame())
        if not df_s1.empty and "NE Name" in df_s1.columns:
            mask = df_s1["NE Name"].astype(str).str.upper().str.contains(site_code, na=False, regex=False)
            for _, row in df_s1[mask].head(10).iterrows():
                s1_data.append({
                    "s1_id": str(row.get("S1 Interface ID", "-")),
                    "status": str(row.get("S1 Interface Status", "-")),
                    "sctp_status": str(row.get("SCTP Link Status", "-")),
                    "mme": str(row.get("Served GUMMEIs", "-")),
                    "local_ip": str(row.get("Local IP Address of SCTP", "-")),
                    "peer_ip": str(row.get("Peer IP Address of SCTP", "-")),
                })
        result["s1_interfaces"] = s1_data

        return result

    # ═══════════════════════════════════════════
    #  TOPOLOGY GRAPH — X2 neighbor network
    # ═══════════════════════════════════════════
    @staticmethod
    def get_topology_data(center_site=None, max_nodes=150):
        """Build network topology from X2 interface data with health scoring."""
        import re
        nodes = {}
        edges = []
        seen_edges = set()
        # Track faults per node
        node_faults = defaultdict(int)
        node_links = defaultdict(int)

        for key in ["4G_LTE_X2_Interface_Report", "5G_NR_X2_Interface_Report"]:
            df = DATA_STORE.get(key, pd.DataFrame())
            if df.empty or "Local NE Name" not in df.columns:
                continue
            tech = "4G" if "LTE" in key else "5G"
            for _, row in df.iterrows():
                local_ne = str(row.get("Local NE Name", ""))
                peer_ne = str(row.get("Peer NE Name", ""))
                local_code = AnalyticsService._extract_site_from_ne(local_ne)
                peer_code = AnalyticsService._extract_site_from_ne(peer_ne)
                if not local_code or not peer_code or local_code == peer_code:
                    continue

                # Add nodes
                if local_code not in nodes:
                    nodes[local_code] = {"id": local_code, "label": local_code, "tech": tech}
                if peer_code not in nodes:
                    nodes[peer_code] = {"id": peer_code, "label": peer_code, "tech": tech}

                # Add edge (deduplicate)
                edge_key = tuple(sorted([local_code, peer_code]))
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    x2_status = str(row.get("Local X2 Interface Status", "-"))
                    sctp = str(row.get("Local SCTP Link Status", row.get("SCTP Link Status", "-")))
                    is_fault = not (x2_status == "Normal" and sctp == "Up")
                    edges.append({
                        "from": local_code, "to": peer_code,
                        "status": "fault" if is_fault else "ok",
                        "x2_status": x2_status,
                        "sctp_status": sctp,
                        "tech": tech,
                    })
                    # Track per-node stats
                    node_links[local_code] += 1
                    node_links[peer_code] += 1
                    if is_fault:
                        node_faults[local_code] += 1
                        node_faults[peer_code] += 1

        # Assign health status to each node
        for nid, node in nodes.items():
            total = node_links.get(nid, 0)
            faults = node_faults.get(nid, 0)
            node["total_links"] = total
            node["fault_count"] = faults
            if faults == 0:
                node["health"] = "healthy"
            elif faults <= total * 0.3:
                node["health"] = "warning"
            else:
                node["health"] = "critical"

        # If center_site specified, filter to neighbors within 2 hops
        if center_site:
            center_site = center_site.strip().upper()
            m = re.match(r'^[345]?[A-Z](\d{2}[A-Z]\d{3,4})', center_site)
            if m:
                center_site = m.group(1)
            hop1 = {center_site}
            for e in edges:
                if e["from"] == center_site:
                    hop1.add(e["to"])
                elif e["to"] == center_site:
                    hop1.add(e["from"])
            hop2 = set(hop1)
            for e in edges:
                if e["from"] in hop1:
                    hop2.add(e["to"])
                elif e["to"] in hop1:
                    hop2.add(e["from"])
            edges = [e for e in edges if e["from"] in hop2 and e["to"] in hop2]
            nodes = {k: v for k, v in nodes.items() if k in hop2}

        # Limit total nodes
        if len(nodes) > max_nodes:
            top_nodes = set(list(nodes.keys())[:max_nodes])
            nodes = {k: v for k, v in nodes.items() if k in top_nodes}
            edges = [e for e in edges if e["from"] in top_nodes and e["to"] in top_nodes]

        # Summary stats
        total_faults = sum(1 for e in edges if e["status"] == "fault")
        return {
            "nodes": list(nodes.values()),
            "edges": edges,
            "summary": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "total_faults": total_faults,
                "healthy_nodes": sum(1 for n in nodes.values() if n["health"] == "healthy"),
                "warning_nodes": sum(1 for n in nodes.values() if n["health"] == "warning"),
                "critical_nodes": sum(1 for n in nodes.values() if n["health"] == "critical"),
            }
        }

    # ═══════════════════════════════════════════
    #  SITE COMPARISON
    # ═══════════════════════════════════════════
    @staticmethod
    def compare_sites(codes):
        """Compare 2-3 sites side by side."""
        import re
        results = []
        for code in codes[:3]:
            code = code.strip().upper()
            m = re.match(r'^[345]?[A-Z](\d{2}[A-Z]\d{3,4})', code)
            if m:
                code = m.group(1)
            profile = AnalyticsService.get_site_profile(code)
            expert = AnalyticsService.get_expert_data(code)

            # Extract summary
            bands = [b["band"] for b in profile.get("config_bands", [])]
            techs_present = list(profile.get("technologies", {}).keys())
            hw_versions = {h["tech"]: h["version"] for h in expert.get("hardware_versions", [])}
            hw_platforms = {h["tech"]: h["platform"] for h in expert.get("hardware_versions", [])}
            rru_models = list(set(r["rru_name"] for r in expert.get("rru_inventory", [])))
            total_cells = sum(len(cells) for cells in profile.get("technologies", {}).values())
            nsa_count = len(expert.get("nsa_anchoring", []))
            x2_count = len(expert.get("x2_neighbors", []))

            results.append({
                "site_code": code,
                "bands": bands,
                "technologies": techs_present,
                "total_cells": total_cells,
                "config_bands": profile.get("config_bands", []),
                "hardware_platforms": hw_platforms,
                "hardware_versions": hw_versions,
                "rru_models": rru_models,
                "nsa_anchor_count": nsa_count,
                "x2_neighbor_count": x2_count,
                "equipment_count": len(profile.get("equipment", [])),
            })
        return results

    # ═══════════════════════════════════════════
    #  WILAYA HEATMAP
    # ═══════════════════════════════════════════
    @staticmethod
    def get_wilaya_heatmap():
        """Compute per-wilaya metrics for heatmap — vectorized."""
        import re
        all_codes = get_all_site_codes()
        wilaya_sites = defaultdict(set)
        for code in all_codes:
            if len(code) >= 2:
                wilaya_sites[code[:2]].add(code)

        wilaya_data = {}
        for wcode, sites in wilaya_sites.items():
            wilaya_data[wcode] = {
                "total_sites": len(sites),
                "cells_2g": 0, "cells_3g": 0, "cells_4g": 0, "cells_5g": 0,
                "equipment_count": 0,
            }

        # Count cells per tech per wilaya — vectorized
        pat = re.compile(r'(\d{2})[A-Z]\d{3,4}')
        for tech_key, tech_label in [("2G", "cells_2g"), ("3G", "cells_3g"), ("4G", "cells_4g"), ("5G", "cells_5g")]:
            df = get_dataframe(tech_key)
            if df.empty:
                continue
            # Concatenate the first string column that looks like it has NE/cell names
            found = False
            for col in df.columns:
                sample = df[col].dropna().astype(str).head(5)
                if any(pat.search(v.upper()) for v in sample):
                    wilayas = df[col].astype(str).str.upper().str.extract(r'(\d{2})[A-Z]\d{3,4}', expand=False).dropna()
                    for wc in wilayas:
                        if wc in wilaya_data:
                            wilaya_data[wc][tech_label] += 1
                    found = True
                    break
            if not found:
                # Fallback: count rows per wilaya from site index
                pass

        # Equipment count per wilaya — vectorized
        df_eq = DATA_STORE.get("Equipment", pd.DataFrame())
        if not df_eq.empty and "Code_site_Standard" in df_eq.columns:
            wilayas = df_eq["Code_site_Standard"].astype(str).str.upper().str.extract(r'(\d{2})[A-Z]\d{3,4}', expand=False).dropna()
            counts = wilayas.value_counts()
            for wc, cnt in counts.items():
                if wc in wilaya_data:
                    wilaya_data[wc]["equipment_count"] = int(cnt)

        return wilaya_data

    # ═══════════════════════════════════════════
    #  NETWORK AUDIT
    # ═══════════════════════════════════════════
    @staticmethod
    def run_network_audit():
        """Cross-dataset network audit: faults, gaps, version mismatches."""
        import re
        audit = {
            "faulty_x2": [],
            "faulty_s1": [],
            "missing_nsa": [],
            "old_firmware": [],
            "cpri_saturation": [],
            "summary": {}
        }

        # 1. Faulty X2 interfaces
        for key in ["4G_LTE_X2_Interface_Report", "5G_NR_X2_Interface_Report"]:
            df = DATA_STORE.get(key, pd.DataFrame())
            if df.empty:
                continue
            tech = "4G" if "LTE" in key else "5G"
            for _, row in df.iterrows():
                status = str(row.get("Local X2 Interface Status", ""))
                sctp = str(row.get("Local SCTP Link Status", row.get("SCTP Link Status", "")))
                if status != "Normal" or sctp != "Up":
                    site = AnalyticsService._extract_site_from_ne(row.get("Local NE Name", ""))
                    peer = AnalyticsService._extract_site_from_ne(row.get("Peer NE Name", ""))
                    if site:
                        audit["faulty_x2"].append({
                            "site": site, "peer": peer, "tech": tech,
                            "x2_status": status, "sctp_status": sctp
                        })

        # 2. Faulty S1 interfaces
        df_s1 = DATA_STORE.get("4G_LTE_S1_Interface_Report", pd.DataFrame())
        if not df_s1.empty:
            for _, row in df_s1.iterrows():
                status = str(row.get("S1 Interface Status", ""))
                sctp = str(row.get("SCTP Link Status", ""))
                if status != "Normal" or sctp != "Up":
                    site = AnalyticsService._extract_site_from_ne(row.get("NE Name", ""))
                    if site:
                        audit["faulty_s1"].append({
                            "site": site, "s1_status": status, "sctp_status": sctp,
                            "mme": str(row.get("Served GUMMEIs", "-"))
                        })

        # 3. Missing NSA anchors (4G sites with no 5G anchor)
        sites_with_4g = set()
        sites_with_nsa = set()
        df_4g_site = DATA_STORE.get("4G_LTE_Site_Report", pd.DataFrame())
        if not df_4g_site.empty and "LTE NE Name" in df_4g_site.columns:
            for val in df_4g_site["LTE NE Name"].dropna():
                code = AnalyticsService._extract_site_from_ne(val)
                if code:
                    sites_with_4g.add(code)
        df_nsa = DATA_STORE.get("4G_LTE_NSA_Report", pd.DataFrame())
        if not df_nsa.empty and "Local NE Name" in df_nsa.columns:
            for val in df_nsa["Local NE Name"].dropna():
                code = AnalyticsService._extract_site_from_ne(val)
                if code:
                    sites_with_nsa.add(code)
        missing_nsa = sites_with_4g - sites_with_nsa
        audit["missing_nsa"] = sorted(missing_nsa)

        # 4. Old firmware
        latest_versions = {}
        for key, ne_col, ver_col, tech in [
            ("4G_LTE_Site_Report", "LTE NE Name", "LTE NE Version", "4G"),
            ("5G_NR_Site_Report", "NR NE Name", "NR NE Version", "5G"),
        ]:
            df = DATA_STORE.get(key, pd.DataFrame())
            if df.empty or ver_col not in df.columns:
                continue
            versions = df[ver_col].dropna().astype(str).unique()
            if len(versions) > 0:
                latest = sorted(versions)[-1]
                latest_versions[tech] = latest
                for _, row in df.iterrows():
                    v = str(row.get(ver_col, ""))
                    if v and v != latest:
                        site = AnalyticsService._extract_site_from_ne(row.get(ne_col, ""))
                        if site:
                            audit["old_firmware"].append({
                                "site": site, "tech": tech,
                                "current": v, "latest": latest
                            })

        # 5. CPRI saturation (>80%)
        for key in ["3G_UMTS_CPRI_Line_Rate_Report", "4G_LTE_CPRI_Line_Rate_Report", "5G_NR_CPRI_Line_Rate_Report"]:
            df = DATA_STORE.get(key, pd.DataFrame())
            if df.empty or "NE Name" not in df.columns:
                continue
            tech = "3G" if "UMTS" in key else ("4G" if "LTE" in key else "5G")
            for _, row in df.iterrows():
                try:
                    line_rate = float(row.get("CPRI Line Rate(Mbit/s)", 0))
                    allocated = float(row.get("Allocated CPRI Bandwidth by Local(Mbit/s)", 0))
                    if line_rate > 0:
                        pct = round(allocated / line_rate * 100, 1)
                        if pct > 80:
                            site = AnalyticsService._extract_site_from_ne(row.get("NE Name", ""))
                            if site:
                                audit["cpri_saturation"].append({
                                    "site": site, "tech": tech,
                                    "port": str(row.get("CPRI Port No.", "-")),
                                    "utilization_pct": pct
                                })
                except (ValueError, TypeError):
                    pass

        # Deduplicate
        seen = set()
        for category in ["faulty_x2", "faulty_s1", "cpri_saturation", "old_firmware"]:
            deduped = []
            for item in audit[category]:
                key = (item.get("site", ""), item.get("peer", ""), item.get("port", ""), category)
                if key not in seen:
                    seen.add(key)
                    deduped.append(item)
            audit[category] = deduped

        audit["summary"] = {
            "faulty_x2_count": len(audit["faulty_x2"]),
            "faulty_s1_count": len(audit["faulty_s1"]),
            "missing_nsa_count": len(audit["missing_nsa"]),
            "old_firmware_count": len(audit["old_firmware"]),
            "cpri_saturation_count": len(audit["cpri_saturation"]),
        }
        return audit

    # ═══════════════════════════════════════════
    #  SMART MULTI-FILTER SEARCH
    # ═══════════════════════════════════════════
    @staticmethod
    def filter_sites(criteria):
        """Filter sites by multiple criteria."""
        import re
        all_codes = get_all_site_codes()
        results = list(all_codes)

        # Wilaya filter
        wilaya = criteria.get("wilaya", "").strip()
        if wilaya:
            results = [c for c in results if c[:2] == wilaya]

        # Technology filter
        tech_filter = criteria.get("technology", "").strip()
        if tech_filter:
            tech_sites = set()
            df = get_dataframe(tech_filter)
            if not df.empty:
                for _, row in df.iterrows():
                    for col in df.columns:
                        m = re.search(r'(\d{2}[A-Z]\d{3,4})', str(row.get(col, "")).upper())
                        if m:
                            tech_sites.add(m.group(1))
                            break
            results = [c for c in results if c in tech_sites]

        # Band filter
        band_filter = criteria.get("band", "").strip()
        if band_filter:
            band_sites = set()
            for tech_key in ["2G", "3G", "4G", "5G"]:
                df = get_dataframe(tech_key)
                if df.empty:
                    continue
                for _, row in df.iterrows():
                    row_str = " ".join(str(v) for v in row.values)
                    if band_filter.upper() in row_str.upper():
                        m = re.search(r'(\d{2}[A-Z]\d{3,4})', row_str.upper())
                        if m:
                            band_sites.add(m.group(1))
            results = [c for c in results if c in band_sites]

        # Platform filter (BTS3900 / BTS5900)
        platform = criteria.get("platform", "").strip()
        if platform:
            plat_sites = set()
            for key in ["4G_LTE_Site_Report", "5G_NR_Site_Report"]:
                df = DATA_STORE.get(key, pd.DataFrame())
                if df.empty:
                    continue
                ver_col = None
                ne_col = None
                for c in df.columns:
                    if 'version' in c.lower():
                        ver_col = c
                    if 'ne name' in c.lower():
                        ne_col = c
                if ver_col and ne_col:
                    mask = df[ver_col].astype(str).str.contains(platform, na=False, case=False)
                    for _, row in df[mask].iterrows():
                        code = AnalyticsService._extract_site_from_ne(row.get(ne_col, ""))
                        if code:
                            plat_sites.add(code)
            results = [c for c in results if c in plat_sites]

        # Build result with basic info
        output = []
        for code in sorted(results)[:200]:
            output.append({"site_code": code, "wilaya": code[:2]})

        return {"sites": output, "total": len(results)}

    # ═══════════════════════════════════════════
    #  FREQUENCY / CARRIER PLANNING
    # ═══════════════════════════════════════════
    @staticmethod
    def get_frequency_plan(site_code):
        """Get per-sector carrier/frequency allocation for a site."""
        import re
        site_code = site_code.strip().upper()
        m = re.match(r'^[345]?[A-Z](\d{2}[A-Z]\d{3,4})', site_code)
        if m:
            site_code = m.group(1)

        plan = {"site_code": site_code, "carriers_2g": [], "cells_3g": [], "cells_4g": [], "cells_5g": []}

        # 2G Carriers
        df_2g = DATA_STORE.get("2G_GSM_Carrier_Report", pd.DataFrame())
        if not df_2g.empty:
            for _, row in df_2g.iterrows():
                row_str = " ".join(str(v) for v in row.values).upper()
                if site_code in row_str:
                    plan["carriers_2g"].append({
                        "cell_name": str(row.get("Cell Name", row.get("cell_name", "-"))),
                        "bcch": str(row.get("BCCH Freq No", row.get("BCCHNo", "-"))),
                        "trx": str(row.get("TRX No", "-")),
                        "hopping": str(row.get("Hopping Type", "-")),
                        "tsc": str(row.get("TSC", "-")),
                        "power": str(row.get("Max Power Level", "-")),
                    })

        # 3G Cells
        df_3g = DATA_STORE.get("3G_UMTS_Cell_Report", pd.DataFrame())
        if not df_3g.empty:
            for _, row in df_3g.iterrows():
                row_str = " ".join(str(v) for v in row.values).upper()
                if site_code in row_str:
                    plan["cells_3g"].append({
                        "cell_name": str(row.get("Cell Name", "-")),
                        "ul_freq": str(row.get("Ul Freq", "-")),
                        "dl_freq": str(row.get("Dl Freq", "-")),
                        "max_power": str(row.get("Max Power", "-")),
                        "hsdpa": str(row.get("HSDPA OpState", "-")),
                        "hsupa": str(row.get("HSUPA OpState", "-")),
                        "lac": str(row.get("LAC", "-")),
                    })

        # 4G Cells
        df_4g = DATA_STORE.get("4G_LTE_Cell_Report", pd.DataFrame())
        if not df_4g.empty:
            for _, row in df_4g.iterrows():
                row_str = " ".join(str(v) for v in row.values).upper()
                if site_code in row_str:
                    plan["cells_4g"].append({
                        "cell_name": str(row.get("Cell Name", "-")),
                        "band": str(row.get("Frequency Band", "-")),
                        "tac": str(row.get("TAC", "-")),
                        "pci": str(row.get("Cell ID", "-")),
                        "status": str(row.get("Availability Status", "-")),
                        "admin": str(row.get("Administrative Status", "-")),
                    })

        # 5G Cells
        df_5g = DATA_STORE.get("5G_NR_Cell_Report", pd.DataFrame())
        if not df_5g.empty:
            for _, row in df_5g.iterrows():
                row_str = " ".join(str(v) for v in row.values).upper()
                if site_code in row_str:
                    plan["cells_5g"].append({
                        "cell_name": str(row.get("Cell Name", "-")),
                        "band": str(row.get("Frequency Band", "-")),
                        "tac": str(row.get("TAC", "-")),
                        "pci": str(row.get("Cell ID", "-")),
                        "status": str(row.get("Availability Status", "-")),
                        "admin": str(row.get("Administrative Status", "-")),
                    })

        return plan

    # ═══════════════════════════════════════════
    #  EQUIPMENT LIFECYCLE TRACKER
    # ═══════════════════════════════════════════
    @staticmethod
    def get_lifecycle_stats():
        """Compute equipment age distribution — vectorized."""
        from datetime import datetime
        df = DATA_STORE.get("Equipment", pd.DataFrame())
        if df.empty or "Date Of Manufacture" not in df.columns:
            return {"age_distribution": {}, "aging_equipment": [], "type_breakdown": {}}

        now = pd.Timestamp.now()
        dates = pd.to_datetime(df["Date Of Manufacture"], errors='coerce')
        age_days = (now - dates).dt.days
        age_years = age_days / 365.25

        # Bin ages
        bins = [-float('inf'), 1, 3, 5, 7, float('inf')]
        labels = ["<1yr", "1-3yr", "3-5yr", "5-7yr", ">7yr"]
        buckets = pd.cut(age_years, bins=bins, labels=labels)

        # Overall distribution
        counts = buckets.value_counts()
        unknown = int(buckets.isna().sum())
        age_dist = {lbl: int(counts.get(lbl, 0)) for lbl in labels}
        age_dist["Unknown"] = unknown

        # Type breakdown
        type_breakdown = {}
        if "EquipeType" in df.columns:
            df_temp = df.copy()
            df_temp["_bucket"] = buckets
            for eq_type, grp in df_temp.groupby("EquipeType"):
                bc = grp["_bucket"].value_counts()
                type_breakdown[str(eq_type)] = {lbl: int(bc.get(lbl, 0)) for lbl in labels}

        # Aging equipment (>7 years) — sample only
        aging = []
        mask = age_years > 7
        if mask.any():
            old_df = df[mask].head(100)
            old_ages = age_years[mask].head(100)
            for (_, row), ay in zip(old_df.iterrows(), old_ages):
                aging.append({
                    "site": str(row.get("Code_site_Standard", "-")),
                    "equipment": str(row.get("Equipment", "-")),
                    "type": str(row.get("EquipeType", "-")),
                    "manufactured": str(row.get("Date Of Manufacture", "-"))[:10],
                    "age_years": round(float(ay), 1)
                })
            aging.sort(key=lambda x: -x.get("age_years", 0))

        return {
            "age_distribution": age_dist,
            "aging_equipment": aging[:100],
            "type_breakdown": type_breakdown,
            "total_equipment": len(df),
        }
