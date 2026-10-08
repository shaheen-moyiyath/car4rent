from flask import Blueprint, request, jsonify
from datetime import datetime, date
from database import Database
from services.fine_calculator import FineCalculatorService

booking_bp = Blueprint('bookings', __name__, url_prefix='/api/bookings')

@booking_bp.route('', methods=['GET'])
def get_bookings():
    client_id = request.args.get('client_id')
    owner_id = request.args.get('owner_id')
    status = request.args.get('status')

    sql = """
        SELECT b.*, v.vehicle_name, v.location, v.price_per_day, v.image_url,
               u_client.name as client_name, u_client.email as client_email, u_client.phone as client_phone,
               u_owner.name as owner_name, u_owner.phone as owner_phone,
               p.payment_status, p.payment_method, p.transaction_id,
               f.fine_id, f.fine_amount, f.reason as fine_reason, f.payment_status as fine_status
        FROM Booking b
        JOIN Vehicle v ON b.vehicle_id = v.vehicle_id
        JOIN User u_client ON b.client_id = u_client.user_id
        JOIN User u_owner ON v.owner_id = u_owner.user_id
        LEFT JOIN Payment p ON b.booking_id = p.booking_id
        LEFT JOIN Fine f ON b.booking_id = f.booking_id
        WHERE 1=1
    """
    params = []
    if client_id:
        sql += " AND b.client_id = %s"
        params.append(client_id)
    if owner_id:
        sql += " AND v.owner_id = %s"
        params.append(owner_id)
    if status:
        sql += " AND b.status = %s"
        params.append(status)

    sql += " ORDER BY b.booking_id DESC"
    bookings = Database.execute_query(sql, tuple(params))
    
    for b in bookings:
        b['total_amount'] = float(b['total_amount'])
        if b['fine_amount'] is not None:
            b['fine_amount'] = float(b['fine_amount'])

    return jsonify({"success": True, "bookings": bookings, "total": len(bookings)})

@booking_bp.route('/<int:booking_id>', methods=['GET'])
def get_booking_by_id(booking_id):
    sql = """
        SELECT b.*, v.vehicle_name, v.location, v.price_per_day, v.image_url, v.owner_id,
               u_client.name as client_name, u_client.email as client_email, u_client.phone as client_phone,
               u_owner.name as owner_name, u_owner.phone as owner_phone,
               p.payment_status, p.payment_method, p.transaction_id,
               f.fine_id, f.fine_amount, f.reason as fine_reason, f.payment_status as fine_status
        FROM Booking b
        JOIN Vehicle v ON b.vehicle_id = v.vehicle_id
        JOIN User u_client ON b.client_id = u_client.user_id
        JOIN User u_owner ON v.owner_id = u_owner.user_id
        LEFT JOIN Payment p ON b.booking_id = p.booking_id
        LEFT JOIN Fine f ON b.booking_id = f.booking_id
        WHERE b.booking_id = %s
    """
    bookings = Database.execute_query(sql, (booking_id,))
    if not bookings:
        return jsonify({"success": False, "error": "Booking not found"}), 404
    
    b = bookings[0]
    b['total_amount'] = float(b['total_amount'])
    return jsonify({"success": True, "booking": b})

@booking_bp.route('', methods=['POST'])
def create_booking():
    data = request.get_json() or {}
    client_id = data.get('client_id')
    vehicle_id = data.get('vehicle_id')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')

    if not all([client_id, vehicle_id, start_date_str, end_date_str]):
        return jsonify({"success": False, "error": "Missing booking details"}), 400

    # Fetch vehicle price
    vehicle = Database.execute_query("SELECT price_per_day, availability FROM Vehicle WHERE vehicle_id = %s", (vehicle_id,))
    if not vehicle:
        return jsonify({"success": False, "error": "Vehicle not found"}), 404
    
    start_d = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_d = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    days = (end_d - start_d).days
    if days <= 0:
        days = 1 # Minimum 1 day rental

    price_per_day = float(vehicle[0]['price_per_day'])
    total_amount = round(days * price_per_day, 2)

    sql = """
        INSERT INTO Booking (client_id, vehicle_id, start_date, end_date, booking_date, total_amount, status)
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s, 'Pending')
    """
    res = Database.execute_query(sql, (client_id, vehicle_id, start_date_str, end_date_str, total_amount))
    booking_id = res.get('last_id')

    return jsonify({
        "success": True,
        "message": "Booking created successfully. Please proceed to payment.",
        "booking_id": booking_id,
        "total_amount": total_amount,
        "days": days
    }), 201

@booking_bp.route('/<int:booking_id>/status', methods=['PATCH'])
def update_booking_status(booking_id):
    data = request.get_json() or {}
    status = data.get('status')
    
    if status not in ['Pending', 'Approved', 'Rejected', 'Active', 'Completed', 'Cancelled']:
        return jsonify({"success": False, "error": "Invalid booking status"}), 400
        
    Database.execute_query("UPDATE Booking SET status = %s WHERE booking_id = %s", (status, booking_id))
    return jsonify({"success": True, "message": f"Booking status updated to {status}"})

@booking_bp.route('/<int:booking_id>/return', methods=['POST'])
def return_vehicle(booking_id):
    """
    Trigger vehicle return flow:
    1. Checks overdue fine via FineCalculatorService.
    2. Updates booking status to 'Completed'.
    3. Releases vehicle availability to 'Available'.
    """
    data = request.get_json() or {}
    return_date = data.get('return_date') # Optional custom return date for testing

    booking = Database.execute_query("SELECT vehicle_id FROM Booking WHERE booking_id = %s", (booking_id,))
    if not booking:
        return jsonify({"success": False, "error": "Booking not found"}), 404
        
    vehicle_id = booking[0]['vehicle_id']

    # Automated Fine Calculation
    fine_result = FineCalculatorService.apply_and_record_fine(booking_id, return_date)

    # Complete booking
    Database.execute_query("UPDATE Booking SET status = 'Completed' WHERE booking_id = %s", (booking_id,))
    # Release vehicle
    Database.execute_query("UPDATE Vehicle SET availability = 'Available' WHERE vehicle_id = %s", (vehicle_id,))

    return jsonify({
        "success": True,
        "message": "Vehicle returned and booking marked as completed.",
        "fine_details": fine_result
    })
