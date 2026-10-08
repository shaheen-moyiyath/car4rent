from flask import Blueprint, request, jsonify
from database import Database
from services.fine_calculator import FineCalculatorService

fine_bp = Blueprint('fines', __name__, url_prefix='/api/fines')

@fine_bp.route('', methods=['GET'])
def list_fines():
    client_id = request.args.get('client_id')
    owner_id = request.args.get('owner_id')
    
    sql = """
        SELECT f.*, b.client_id, b.vehicle_id, b.start_date, b.end_date,
               v.vehicle_name, v.price_per_day,
               u.name as client_name, u.email as client_email
        FROM Fine f
        JOIN Booking b ON f.booking_id = b.booking_id
        JOIN Vehicle v ON b.vehicle_id = v.vehicle_id
        JOIN User u ON b.client_id = u.user_id
        WHERE 1=1
    """
    params = []
    if client_id:
        sql += " AND b.client_id = %s"
        params.append(client_id)
    if owner_id:
        sql += " AND v.owner_id = %s"
        params.append(owner_id)
        
    sql += " ORDER BY f.fine_id DESC"
    fines = Database.execute_query(sql, tuple(params))
    for f in fines:
        f['fine_amount'] = float(f['fine_amount'])
        f['price_per_day'] = float(f['price_per_day'])
        
    return jsonify({"success": True, "fines": fines, "total": len(fines)})

@fine_bp.route('/calculate/<int:booking_id>', methods=['POST'])
def calculate_fine(booking_id):
    data = request.get_json() or {}
    return_date = data.get('return_date')
    result = FineCalculatorService.calculate_overdue_fine(booking_id, return_date)
    return jsonify(result)

@fine_bp.route('/<int:fine_id>/pay', methods=['POST'])
def pay_fine(fine_id):
    fine = Database.execute_query("SELECT * FROM Fine WHERE fine_id = %s", (fine_id,))
    if not fine:
        return jsonify({"success": False, "error": "Fine record not found"}), 404
        
    Database.execute_query("UPDATE Fine SET payment_status = 'Paid' WHERE fine_id = %s", (fine_id,))
    return jsonify({"success": True, "message": "Fine paid successfully", "fine_id": fine_id})
