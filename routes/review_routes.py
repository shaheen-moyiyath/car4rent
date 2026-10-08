from flask import Blueprint, request, jsonify
from datetime import date
from database import Database

review_bp = Blueprint('reviews', __name__, url_prefix='/api/reviews')

@review_bp.route('', methods=['POST'])
def submit_review():
    data = request.get_json() or {}
    client_id = data.get('client_id')
    vehicle_id = data.get('vehicle_id')
    booking_id = data.get('booking_id')
    rating = data.get('rating')
    review_text = data.get('review_text', '').strip()

    if not all([client_id, vehicle_id, booking_id, rating]):
        return jsonify({"success": False, "error": "client_id, vehicle_id, booking_id, and rating are required"}), 400

    rating_val = int(rating)
    if rating_val < 1 or rating_val > 5:
        return jsonify({"success": False, "error": "Rating must be between 1 and 5"}), 400

    # Check if already reviewed this booking
    existing = Database.execute_query(
        "SELECT review_id FROM Review WHERE booking_id = %s AND client_id = %s",
        (booking_id, client_id)
    )
    if existing:
        return jsonify({"success": False, "error": "You have already reviewed this booking"}), 409

    review_date = date.today().strftime('%Y-%m-%d')
    sql = """
        INSERT INTO Review (client_id, vehicle_id, booking_id, rating, review_text, review_date)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    res = Database.execute_query(sql, (client_id, vehicle_id, booking_id, rating_val, review_text, review_date))

    return jsonify({
        "success": True,
        "message": "Thank you for your feedback!",
        "review_id": res.get('last_id'),
        "rating": rating_val
    }), 201

@review_bp.route('/vehicle/<int:vehicle_id>', methods=['GET'])
def get_vehicle_reviews(vehicle_id):
    sql = """
        SELECT r.*, u.name as client_name
        FROM Review r
        JOIN User u ON r.client_id = u.user_id
        WHERE r.vehicle_id = %s
        ORDER BY r.review_id DESC
    """
    reviews = Database.execute_query(sql, (vehicle_id,))
    return jsonify({"success": True, "reviews": reviews, "total": len(reviews)})

@review_bp.route('/owner/<int:owner_id>', methods=['GET'])
def get_owner_reviews(owner_id):
    sql = """
        SELECT r.*, v.vehicle_name, u.name as client_name
        FROM Review r
        JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
        JOIN User u ON r.client_id = u.user_id
        WHERE v.owner_id = %s
        ORDER BY r.review_id DESC
    """
    reviews = Database.execute_query(sql, (owner_id,))
    return jsonify({"success": True, "reviews": reviews, "total": len(reviews)})
