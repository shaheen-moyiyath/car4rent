from flask import Blueprint, request, jsonify, session
from database import Database

vehicle_bp = Blueprint('vehicles', __name__, url_prefix='/api/vehicles')

@vehicle_bp.route('', methods=['GET'])
def get_vehicles():
    """
    Search and filter vehicles by category, price_max, location, and availability.
    """
    category_id = request.args.get('category_id')
    price_max = request.args.get('price_max')
    location = request.args.get('location', '').strip()
    availability = request.args.get('availability', '').strip()
    owner_id = request.args.get('owner_id')
    search = request.args.get('search', '').strip()

    sql = """
        SELECT v.*, c.category_name, u.name as owner_name, u.phone as owner_phone,
               COALESCE(AVG(r.rating), 4.8) as avg_rating,
               COUNT(r.review_id) as review_count
        FROM Vehicle v
        JOIN Vehicle_Category c ON v.category_id = c.category_id
        JOIN User u ON v.owner_id = u.user_id
        LEFT JOIN Review r ON v.vehicle_id = r.vehicle_id
        WHERE 1=1
    """
    params = []

    if category_id:
        sql += " AND v.category_id = %s"
        params.append(category_id)
    if price_max:
        sql += " AND v.price_per_day <= %s"
        params.append(float(price_max))
    if location:
        sql += " AND v.location LIKE %s"
        params.append(f"%{location}%")
    if availability:
        sql += " AND v.availability = %s"
        params.append(availability)
    if owner_id:
        sql += " AND v.owner_id = %s"
        params.append(owner_id)
    if search:
        sql += " AND (v.vehicle_name LIKE %s OR v.location LIKE %s OR c.category_name LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    sql += """
        GROUP BY v.vehicle_id, c.category_name, u.name, u.phone
        ORDER BY v.vehicle_id DESC
    """

    vehicles = Database.execute_query(sql, tuple(params))
    for v in vehicles:
        v['price_per_day'] = float(v['price_per_day'])
        v['avg_rating'] = round(float(v['avg_rating']), 1)
        v['mileage'] = int(v['mileage'])

    return jsonify({"success": True, "vehicles": vehicles, "total": len(vehicles)})

@vehicle_bp.route('/<int:vehicle_id>', methods=['GET'])
def get_vehicle_details(vehicle_id):
    sql = """
        SELECT v.*, c.category_name, c.description as category_desc, u.name as owner_name, u.email as owner_email, u.phone as owner_phone,
               COALESCE(AVG(r.rating), 5.0) as avg_rating,
               COUNT(r.review_id) as review_count
        FROM Vehicle v
        JOIN Vehicle_Category c ON v.category_id = c.category_id
        JOIN User u ON v.owner_id = u.user_id
        LEFT JOIN Review r ON v.vehicle_id = r.vehicle_id
        WHERE v.vehicle_id = %s
        GROUP BY v.vehicle_id, c.category_name, c.description, u.name, u.email, u.phone
    """
    vehicles = Database.execute_query(sql, (vehicle_id,))
    if not vehicles:
        return jsonify({"success": False, "error": "Vehicle not found"}), 404

    v = vehicles[0]
    v['price_per_day'] = float(v['price_per_day'])
    v['avg_rating'] = round(float(v['avg_rating']), 1)
    
    # Fetch recent reviews
    reviews = Database.execute_query("""
        SELECT r.*, u.name as client_name
        FROM Review r
        JOIN User u ON r.client_id = u.user_id
        WHERE r.vehicle_id = %s
        ORDER BY r.review_id DESC LIMIT 10
    """, (vehicle_id,))
    v['reviews'] = reviews

    return jsonify({"success": True, "vehicle": v})

@vehicle_bp.route('', methods=['POST'])
def add_vehicle():
    data = request.get_json() or {}
    owner_id = data.get('owner_id')
    category_id = data.get('category_id')
    vehicle_name = data.get('vehicle_name', '').strip()
    location = data.get('location', '').strip()
    price_per_day = data.get('price_per_day')
    mileage = data.get('mileage', 0)
    vehicle_3d_view = data.get('vehicle_3d_view', '{"color":"#1e3a8a","modelType":"sedan","metallic":0.8}')
    gps_device_id = data.get('gps_device_id', f"GPS-DEV-{vehicle_name[:3].upper()}")
    image_url = data.get('image_url', 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80')

    if not all([owner_id, category_id, vehicle_name, location, price_per_day]):
        return jsonify({"success": False, "error": "Missing required vehicle parameters"}), 400

    sql = """
        INSERT INTO Vehicle (owner_id, category_id, vehicle_name, location, price_per_day, availability, mileage, vehicle_3d_view, gps_device_id, image_url)
        VALUES (%s, %s, %s, %s, %s, 'Available', %s, %s, %s, %s)
    """
    res = Database.execute_query(sql, (
        owner_id, category_id, vehicle_name, location, float(price_per_day),
        int(mileage), vehicle_3d_view, gps_device_id, image_url
    ))
    vehicle_id = res.get('last_id')

    # Seed initial GPS point
    from services.gps_service import GPSTrackingService
    GPSTrackingService.record_gps_telemetry(vehicle_id, 37.7749, -122.4194, 0.0)

    # Seed initial maintenance record
    from services.maintenance_service import MaintenanceService
    MaintenanceService.log_maintenance_service(vehicle_id, "Initial Safety Inspection", int(mileage), 10000)

    return jsonify({"success": True, "message": "Vehicle listed successfully", "vehicle_id": vehicle_id}), 201

@vehicle_bp.route('/<int:vehicle_id>', methods=['PUT'])
def update_vehicle(vehicle_id):
    data = request.get_json() or {}
    sql = """
        UPDATE Vehicle SET
            vehicle_name = COALESCE(%s, vehicle_name),
            category_id = COALESCE(%s, category_id),
            location = COALESCE(%s, location),
            price_per_day = COALESCE(%s, price_per_day),
            availability = COALESCE(%s, availability),
            mileage = COALESCE(%s, mileage),
            vehicle_3d_view = COALESCE(%s, vehicle_3d_view),
            gps_device_id = COALESCE(%s, gps_device_id),
            image_url = COALESCE(%s, image_url)
        WHERE vehicle_id = %s
    """
    Database.execute_query(sql, (
        data.get('vehicle_name'),
        data.get('category_id'),
        data.get('location'),
        data.get('price_per_day'),
        data.get('availability'),
        data.get('mileage'),
        data.get('vehicle_3d_view'),
        data.get('gps_device_id'),
        data.get('image_url'),
        vehicle_id
    ))
    return jsonify({"success": True, "message": "Vehicle updated successfully"})

@vehicle_bp.route('/<int:vehicle_id>', methods=['DELETE'])
def delete_vehicle(vehicle_id):
    Database.execute_query("DELETE FROM Vehicle WHERE vehicle_id = %s", (vehicle_id,))
    return jsonify({"success": True, "message": "Vehicle deleted successfully"})

@vehicle_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Database.execute_query("SELECT * FROM Vehicle_Category ORDER BY category_id ASC")
    return jsonify({"success": True, "categories": categories})
