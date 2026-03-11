from flask import Blueprint, jsonify, request, session
from flask_wtf.csrf import generate_csrf
from app.services.user_service import UserService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/csrf', methods=['GET'])
def get_csrf():
    token = generate_csrf()
    return jsonify({"csrf_token": token})

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(force=True, silent=True)
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Missing credentials"}), 400
        
    user = UserService.authenticate(data['username'], data['password'])
    
    if user:
        session['user'] = user['username']
        session['role'] = user['role']
        return jsonify({"message": "Login successful", "user": user})
        
    return jsonify({"error": "Invalid username or password"}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})

@auth_bp.route('/session', methods=['GET'])
def check_session():
    if 'user' in session:
        return jsonify({"user": session['user'], "role": session.get('role')})
    return jsonify({"error": "Not logged in"}), 401
