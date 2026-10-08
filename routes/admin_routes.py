from flask import Blueprint, request, jsonify
from database import Database, hash_password

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/stats', methods=['GET'])
def get_system_stats():
    """Returns platform-wide metrics and revenue overview."""
    total_users = Database.execute_query("SELECT COUNT(*) as count FROM User")[0]['count']
    total_vehicles = Database.execute_query("SELECT COUNT(*) as count FROM Vehicle")[0]['count']
    total_bookings = Database.execute_query("SELECT COUNT(*) as count FROM Booking")[0]['count']
    
    revenue_res = Database.execute_query(
        "SELECT COALESCE(SUM(amount), 0) as total_rev FROM Payment WHERE payment_status = 'Completed'"
    )
    total_revenue = float(revenue_res[0]['total_rev']) if revenue_res else 0.0

    fines_res = Database.execute_query(
        "SELECT COALESCE(SUM(fine_amount), 0) as total_fines FROM Fine WHERE payment_status = 'Paid'"
    )
    total_fines = float(fines_res[0]['total_fines']) if fines_res else 0.0

    active_rentals = Database.execute_query(
        "SELECT COUNT(*) as count FROM Booking WHERE status = 'Active'"
    )[0]['count']

    # Revenue by vehicle category
    category_revenue = Database.execute_query("""
        SELECT c.category_name, COALESCE(SUM(p.amount), 0) as revenue
        FROM Vehicle_Category c
        JOIN Vehicle v ON c.category_id = v.category_id
        JOIN Booking b ON v.vehicle_id = b.vehicle_id
        JOIN Payment p ON b.booking_id = p.booking_id AND p.payment_status = 'Completed'
        GROUP BY c.category_name
    """)
    for cr in category_revenue:
        cr['revenue'] = float(cr['revenue'])

    return jsonify({
        "success": True,
        "metrics": {
            "total_users": total_users,
            "total_vehicles": total_vehicles,
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "total_fines_collected": total_fines,
            "active_rentals": active_rentals
        },
        "category_revenue": category_revenue
    })

# --- User Management ---
@admin_bp.route('/users', methods=['GET'])
def list_users():
    users = Database.execute_query("SELECT user_id, role, email, phone, name, created_at FROM User ORDER BY user_id DESC")
    return jsonify({"success": True, "users": users, "total": len(users)})

@admin_bp.route('/users', methods=['POST'])
def add_user():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'Client')

    if not all([name, email, phone, password]):
        return jsonify({"success": False, "error": "All fields required"}), 400

    existing = Database.execute_query("SELECT user_id FROM User WHERE email = %s", (email,))
    if existing:
        return jsonify({"success": False, "error": "Email already exists"}), 409

    pwd_hash = hash_password(password)
    res = Database.execute_query(
        "INSERT INTO User (role, email, phone, name, password) VALUES (%s, %s, %s, %s, %s)",
        (role, email, phone, name, pwd_hash)
    )
    return jsonify({"success": True, "message": "User created", "user_id": res.get('last_id')}), 201

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json() or {}
    sql = """
        UPDATE User SET
            name = COALESCE(%s, name),
            email = COALESCE(%s, email),
            phone = COALESCE(%s, phone),
            role = COALESCE(%s, role)
        WHERE user_id = %s
    """
    Database.execute_query(sql, (data.get('name'), data.get('email'), data.get('phone'), data.get('role'), user_id))
    return jsonify({"success": True, "message": "User updated successfully"})

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    Database.execute_query("DELETE FROM User WHERE user_id = %s", (user_id,))
    return jsonify({"success": True, "message": "User deleted successfully"})

# --- Category Management ---
@admin_bp.route('/categories', methods=['POST'])
def add_category():
    data = request.get_json() or {}
    name = data.get('category_name', '').strip()
    desc = data.get('description', '').strip()
    if not name:
        return jsonify({"success": False, "error": "Category name required"}), 400
    
    res = Database.execute_query(
        "INSERT INTO Vehicle_Category (category_name, description) VALUES (%s, %s)",
        (name, desc)
    )
    return jsonify({"success": True, "message": "Category created", "category_id": res.get('last_id')}), 201

@admin_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    data = request.get_json() or {}
    sql = """
        UPDATE Vehicle_Category SET
            category_name = COALESCE(%s, category_name),
            description = COALESCE(%s, description)
        WHERE category_id = %s
    """
    Database.execute_query(sql, (data.get('category_name'), data.get('description'), category_id))
    return jsonify({"success": True, "message": "Category updated successfully"})

@admin_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    # Check if vehicles assigned
    cars = Database.execute_query("SELECT COUNT(*) as count FROM Vehicle WHERE category_id = %s", (category_id,))
    if cars[0]['count'] > 0:
        return jsonify({"success": False, "error": "Cannot delete category containing existing vehicles"}), 400

    Database.execute_query("DELETE FROM Vehicle_Category WHERE category_id = %s", (category_id,))
    return jsonify({"success": True, "message": "Category deleted successfully"})

# --- System Logs ---
@admin_bp.route('/logs', methods=['GET'])
def get_system_logs():
    recent_bookings = Database.execute_query("""
        SELECT b.booking_id, b.start_date, b.end_date, b.total_amount, b.status, b.booking_date,
               u.name as client_name, v.vehicle_name
        FROM Booking b
        JOIN User u ON b.client_id = u.user_id
        JOIN Vehicle v ON b.vehicle_id = v.vehicle_id
        ORDER BY b.booking_id DESC LIMIT 15
    """)
    recent_payments = Database.execute_query("""
        SELECT p.*, b.client_id, u.name as client_name
        FROM Payment p
        JOIN Booking b ON p.booking_id = b.booking_id
        JOIN User u ON b.client_id = u.user_id
        ORDER BY p.payment_id DESC LIMIT 15
    """)
    for p in recent_payments:
        p['amount'] = float(p['amount'])
    for b in recent_bookings:
        b['total_amount'] = float(b['total_amount'])

    return jsonify({
        "success": True,
        "recent_bookings": recent_bookings,
        "recent_payments": recent_payments
    })
