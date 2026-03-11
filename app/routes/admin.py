import os
from flask import Blueprint, jsonify, request, session
from app.utils.security import require_auth, require_admin
from app import csrf
import threading

from app.services.data_loader import load_all_data, is_data_loaded
from app.services.analytics import AnalyticsService
from app.services.user_service import UserService

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/status', methods=['GET'])
@require_auth
@require_admin
def admin_status():
    stats = AnalyticsService.get_dashboard_stats()
    return jsonify(stats)

@admin_bp.route('/reload', methods=['POST'])
@require_auth
@require_admin
def reload_data():
    def bg_load():
        load_all_data()
    thread = threading.Thread(target=bg_load)
    thread.start()
    return jsonify({"message": "Data reload started in background"})

@admin_bp.route('/upload', methods=['POST'])
@require_auth
@require_admin
def upload_dataset():
    from app.config import Config
    from app.services.data_loader import load_excel_file, get_cache_path, _build_site_index, _scan_report_dir
    from app import DATA_STORE

    category = request.form.get('dataset')
    files = request.files.getlist('file')

    if not category or not files:
        return jsonify({"error": "Category and at least one file required"}), 400

    # Core file mapping (single-file categories)
    core_map = {
        "2G": "2G.xlsx", "3G": "3G.xlsx", "4G": "4G.xlsx", "5G": "5G.xlsx",
        "Equipment": "RI HUawei 23-12-25.xlsx",
    }

    # Report folder mapping for extended datasets
    report_folder_map = {
        "2G_Reports": "Report_2G",
        "3G_Reports": "Report_3G",
        "4G_Reports": "Report_4G",
        "5G_Reports": "Report_5G",
    }

    results = []

    if category in core_map:
        # Core dataset: save single file with fixed name
        f = files[0]
        target_path = os.path.join(Config.BASE_DIR, core_map[category])
        f.save(target_path)
        cache_path = get_cache_path(target_path)
        if os.path.exists(cache_path):
            os.remove(cache_path)
        DATA_STORE[category] = load_excel_file(target_path)
        results.append(f"{category}: {len(DATA_STORE[category])} rows")

    elif category in report_folder_map:
        # Report datasets: save multiple files to the report folder
        folder_name = report_folder_map[category]
        report_dir = os.path.join(Config.BASE_DIR, folder_name)
        os.makedirs(report_dir, exist_ok=True)

        # Clear old files in the folder
        import glob as _glob
        for old_file in _glob.glob(os.path.join(report_dir, "*.xlsx")):
            old_path_cache = get_cache_path(old_file)
            if os.path.exists(old_path_cache):
                os.remove(old_path_cache)

        for f in files:
            fname = f.filename
            target_path = os.path.join(report_dir, fname)
            f.save(target_path)
            # Remove old cache
            cache_path = get_cache_path(target_path)
            if os.path.exists(cache_path):
                os.remove(cache_path)
            results.append(f"Saved: {fname}")

        # Remove old keys from DATA_STORE for this prefix
        prefix = category.replace("_Reports", "")
        old_keys = [k for k in DATA_STORE if k.startswith(prefix + "_") and k not in ["2G", "3G", "4G", "5G"]]
        for k in old_keys:
            del DATA_STORE[k]

        # Reload the report folder
        _scan_report_dir(folder_name, prefix)

    else:
        return jsonify({"error": f"Unknown category: {category}"}), 400

    # Rebuild site index
    _build_site_index()

    return jsonify({
        "message": f"Upload complete: {len(results)} file(s) processed",
        "details": results
    })

# ═══ USER MANAGEMENT ═══
@admin_bp.route('/users', methods=['GET'])
@require_auth
@require_admin
def list_users():
    users = UserService.list_users()
    return jsonify({"users": users})

@admin_bp.route('/users', methods=['POST'])
@require_auth
@require_admin
def create_user():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Invalid request"}), 400
    username = data.get('username', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'user')
    ok, msg = UserService.create_user(username, password, role)
    if ok:
        return jsonify({"message": msg})
    return jsonify({"error": msg}), 400

@admin_bp.route('/users/password', methods=['POST'])
@require_auth
@require_admin
def change_password():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Invalid request"}), 400
    username = data.get('username', '').strip()
    new_password = data.get('password', '')
    ok, msg = UserService.change_password(username, new_password)
    if ok:
        return jsonify({"message": msg})
    return jsonify({"error": msg}), 400

@admin_bp.route('/users/delete', methods=['POST'])
@require_auth
@require_admin
def delete_user():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Invalid request"}), 400
    username = data.get('username', '').strip()
    ok, msg = UserService.delete_user(username)
    if ok:
        return jsonify({"message": msg})
    return jsonify({"error": msg}), 400
