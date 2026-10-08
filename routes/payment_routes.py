from flask import Blueprint, request, jsonify
from database import Database
from services.payment_gateway import PaymentGatewayService

payment_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@payment_bp.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json() or {}
    booking_id = data.get('booking_id')
    amount = data.get('amount')
    payment_method = data.get('payment_method', 'Credit Card')

    if not booking_id or not amount:
        return jsonify({"success": False, "error": "Booking ID and amount are required"}), 400

    result = PaymentGatewayService.process_payment(booking_id, float(amount), payment_method)
    if not result.get('success'):
        return jsonify(result), 400

    return jsonify(result), 200

@payment_bp.route('/booking/<int:booking_id>', methods=['GET'])
def get_booking_payment(booking_id):
    payments = Database.execute_query(
        "SELECT * FROM Payment WHERE booking_id = %s ORDER BY payment_id DESC",
        (booking_id,)
    )
    if not payments:
        return jsonify({"success": False, "error": "No payment found"}), 404
        
    p = payments[0]
    p['amount'] = float(p['amount'])
    return jsonify({"success": True, "payment": p})
