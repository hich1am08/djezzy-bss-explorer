from flask import Blueprint, jsonify, request, send_file
from app.utils.security import require_auth
from app.services.analytics import AnalyticsService
from app.services.report_generator import generate_batch_report
from app.services.data_loader import is_data_loaded, get_all_dataset_names, get_dataset_page, get_all_site_codes

api_bp = Blueprint('api', __name__)

@api_bp.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok", "data_loaded": is_data_loaded()})

@api_bp.route('/search/global', methods=['GET'])
@require_auth
def search_global():
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 50))
    results = AnalyticsService.search_global(query, limit)
    return jsonify({"results": results, "count": len(results)})

@api_bp.route('/search/parameter', methods=['GET'])
@require_auth
def search_parameter():
    """Search by specific parameter name and value (e.g., TAC=12345)."""
    param_name = request.args.get('param', '')
    param_value = request.args.get('value', '')
    limit = int(request.args.get('limit', 100))
    if not param_name or not param_value:
        return jsonify({"error": "Both 'param' and 'value' are required"}), 400
    results = AnalyticsService.search_by_parameter(param_name, param_value, limit)
    return jsonify({"results": results, "count": len(results), "param": param_name, "value": param_value})

@api_bp.route('/search/site', methods=['GET'])
@require_auth
def search_site():
    site_code = request.args.get('code', '')
    if not site_code:
        return jsonify({"error": "Site code required"}), 400
    profile = AnalyticsService.get_site_profile(site_code)
    return jsonify(profile)

@api_bp.route('/dashboard', methods=['GET'])
@require_auth
def dashboard():
    stats = AnalyticsService.get_dashboard_stats()
    return jsonify(stats)

@api_bp.route('/sites/list', methods=['GET'])
@require_auth
def sites_list():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    search = request.args.get('q', '')
    sites, total = AnalyticsService.get_sites_list(page, per_page, search)
    return jsonify({"sites": sites, "total": total, "page": page, "per_page": per_page})

@api_bp.route('/datasets', methods=['GET'])
@require_auth
def list_datasets():
    names = get_all_dataset_names()
    return jsonify({"datasets": names})

@api_bp.route('/datasets/<name>', methods=['GET'])
@require_auth
def browse_dataset(name):
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    search = request.args.get('q', '')
    rows, total, columns = get_dataset_page(name, page, per_page, search)
    return jsonify({"rows": rows, "total": total, "columns": columns, "page": page, "per_page": per_page})

@api_bp.route('/stats/network', methods=['GET'])
@require_auth
def network_stats():
    stats = AnalyticsService.get_dashboard_stats()
    return jsonify(stats)

@api_bp.route('/batch/search', methods=['POST'])
@require_auth
def batch_search():
    data = request.get_json(force=True, silent=True)
    codes = data.get('codes', []) if data else []
    if not codes:
        return jsonify({"error": "No site codes provided"}), 400
    import re
    clean_codes = []
    for c in codes:
        c = c.strip().upper()
        match = re.match(r'^[345]?[A-Z](\d{2}[A-Z]\d{3,4})', c)
        if match:
            clean_codes.append(match.group(1))
        elif re.match(r'^\d{2}[A-Z]\d{3,4}$', c):
            clean_codes.append(c)
    clean_codes = list(dict.fromkeys(clean_codes))
    results = []
    for code in clean_codes:
        profile = AnalyticsService.get_site_profile(code)
        results.append(profile)
    return jsonify({"results": results, "count": len(results)})

@api_bp.route('/batch/export', methods=['POST'])
@require_auth
def batch_export():
    data = request.get_json(force=True, silent=True)
    codes = data.get('codes', []) if data else []
    if not codes:
        return jsonify({"error": "No site codes provided"}), 400
    import re
    clean_codes = []
    for c in codes:
        c = c.strip().upper()
        match = re.match(r'^[345]?[A-Z](\d{2}[A-Z]\d{3,4})', c)
        if match:
            clean_codes.append(match.group(1))
        elif re.match(r'^\d{2}[A-Z]\d{3,4}$', c):
            clean_codes.append(c)
    clean_codes = list(dict.fromkeys(clean_codes))
    buffer = generate_batch_report(clean_codes)
    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'Djezzy_BSS_Report_{len(clean_codes)}_sites.xlsx'
    )


@api_bp.route('/expert/site', methods=['GET'])
@require_auth
def expert_site():
    site_code = request.args.get('code', '')
    if not site_code:
        return jsonify({"error": "Site code required"}), 400
    data = AnalyticsService.get_expert_data(site_code)
    return jsonify(data)


@api_bp.route('/topology', methods=['GET'])
@require_auth
def topology():
    center = request.args.get('center', None)
    data = AnalyticsService.get_topology_data(center)
    return jsonify(data)


@api_bp.route('/compare', methods=['POST'])
@require_auth
def compare():
    data = request.get_json(force=True, silent=True)
    codes = data.get('codes', []) if data else []
    if not codes or len(codes) < 2:
        return jsonify({"error": "At least 2 site codes required"}), 400
    result = AnalyticsService.compare_sites(codes)
    return jsonify({"sites": result})


@api_bp.route('/heatmap/wilaya', methods=['GET'])
@require_auth
def wilaya_heatmap():
    data = AnalyticsService.get_wilaya_heatmap()
    return jsonify(data)


@api_bp.route('/audit', methods=['GET'])
@require_auth
def network_audit():
    data = AnalyticsService.run_network_audit()
    return jsonify(data)


@api_bp.route('/filter', methods=['POST'])
@require_auth
def filter_sites():
    data = request.get_json(force=True, silent=True) or {}
    result = AnalyticsService.filter_sites(data)
    return jsonify(result)


@api_bp.route('/frequency', methods=['GET'])
@require_auth
def frequency_plan():
    code = request.args.get('code', '')
    if not code:
        return jsonify({"error": "Site code required"}), 400
    data = AnalyticsService.get_frequency_plan(code)
    return jsonify(data)


@api_bp.route('/lifecycle', methods=['GET'])
@require_auth
def lifecycle():
    data = AnalyticsService.get_lifecycle_stats()
    return jsonify(data)
