from flask import Blueprint, request, jsonify, session
from database import Database, hash_password

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'Client').capitalize()
    
    if not all([name, email, phone, password]):
        return jsonify({"success": False, "error": "All fields are required"}), 400
    
    if role not in ['Admin', 'Owner', 'Client']:
        return jsonify({"success": False, "error": "Invalid role specified"}), 400
    
    # Check duplicate email
    existing = Database.execute_query("SELECT user_id FROM User WHERE email = %s", (email,))
    if existing:
        return jsonify({"success": False, "error": "Email address is already registered"}), 409
    
    hashed_pwd = hash_password(password)
    sql = """
        INSERT INTO User (role, email, phone, name, password)
        VALUES (%s, %s, %s, %s, %s)
    """
    res = Database.execute_query(sql, (role, email, phone, name, hashed_pwd))
    user_id = res.get('last_id')
    
    user_data = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "phone": phone,
        "role": role
    }
    session['user'] = user_data
    
    return jsonify({
        "success": True,
        "message": f"Account registered successfully as {role}",
        "user": user_data
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    
    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required"}), 400
    
    hashed_pwd = hash_password(password)
    sql = "SELECT user_id, role, email, phone, name, password FROM User WHERE email = %s"
    users = Database.execute_query(sql, (email,))
    
    if not users or users[0]['password'] != hashed_pwd:
        return jsonify({"success": False, "error": "Invalid email or password"}), 401
    
    user = users[0]
    user_data = {
        "user_id": user['user_id'],
        "name": user['name'],
        "email": user['email'],
        "phone": user['phone'],
        "role": user['role']
    }
    session['user'] = user_data
    
    return jsonify({
        "success": True,
        "message": f"Welcome back, {user['name']}",
        "user": user_data
    })

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    user = session.get('user')
    if not user:
        return jsonify({"success": False, "user": None})
    return jsonify({"success": True, "user": user})

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({"success": True, "message": "Logged out successfully"})
