from flask import Blueprint, request, jsonify
from database import Database
from services.gps_service import GPSTrackingService

gps_bp = Blueprint('gps', __name__, url_prefix='/api/gps')

@gps_bp.route('/telemetry', methods=['POST'])
def post_telemetry():
    """Receives IoT GPS telemetry packet from connected vehicle trackers."""
    data = request.get_json() or {}
    vehicle_id = data.get('vehicle_id')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    speed = data.get('speed', 0.0)

    if not vehicle_id or latitude is None or longitude is None:
        return jsonify({"success": False, "error": "vehicle_id, latitude, longitude are required"}), 400

    result = GPSTrackingService.record_gps_telemetry(int(vehicle_id), float(latitude), float(longitude), float(speed))
    return jsonify(result), 201

@gps_bp.route('/vehicle/<int:vehicle_id>/live', methods=['GET'])
def get_live_location(vehicle_id):
    """Returns the latest GPS coordinates and speed for a specific vehicle."""
    pos = GPSTrackingService.get_latest_position(vehicle_id)
    return jsonify(pos)

@gps_bp.route('/vehicle/<int:vehicle_id>/history', methods=['GET'])
def get_route_history(vehicle_id):
    """Returns the GPS route history waypoints for a specific vehicle."""
    limit = request.args.get('limit', 50)
    history = GPSTrackingService.get_vehicle_route_history(vehicle_id, int(limit))
    return jsonify({"success": True, "vehicle_id": vehicle_id, "history": history})

@gps_bp.route('/owner/<int:owner_id>/fleet', methods=['GET'])
def get_owner_fleet(owner_id):
    """Returns the live positions of all vehicles owned by an owner."""
    fleet = GPSTrackingService.get_owner_fleet_live_positions(owner_id)
    return jsonify({"success": True, "owner_id": owner_id, "fleet": fleet})

@gps_bp.route('/vehicle/<int:vehicle_id>/simulate-step', methods=['POST'])
def simulate_step(vehicle_id):
    """Simulates real-time driving progression for demo."""
    result = GPSTrackingService.simulate_telemetry_step(vehicle_id)
    return jsonify(result)
