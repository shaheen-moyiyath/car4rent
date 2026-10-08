from flask import Blueprint, request, jsonify
from database import Database
from services.maintenance_service import MaintenanceService

maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/api/maintenance')

@maintenance_bp.route('/vehicle/<int:vehicle_id>', methods=['GET'])
def get_vehicle_maintenance(vehicle_id):
    status = MaintenanceService.check_vehicle_maintenance_status(vehicle_id)
    history = Database.execute_query(
        "SELECT * FROM Maintenance WHERE vehicle_id = %s ORDER BY maintenance_id DESC",
        (vehicle_id,)
    )
    return jsonify({
        "success": True,
        "current_status": status,
        "history": history
    })

@maintenance_bp.route('/owner/<int:owner_id>/alerts', methods=['GET'])
def get_owner_alerts(owner_id):
    alerts = MaintenanceService.get_owner_fleet_alerts(owner_id)
    return jsonify({"success": True, "owner_id": owner_id, "alerts": alerts})

@maintenance_bp.route('/service', methods=['POST'])
def log_service():
    data = request.get_json() or {}
    vehicle_id = data.get('vehicle_id')
    service_type = data.get('service_type', 'Routine Service')
    current_km = data.get('current_km', 0)
    next_service_interval_km = data.get('next_service_interval_km', 10000)

    if not vehicle_id:
        return jsonify({"success": False, "error": "Vehicle ID is required"}), 400

    result = MaintenanceService.log_maintenance_service(
        int(vehicle_id),
        service_type,
        int(current_km),
        int(next_service_interval_km)
    )
    return jsonify(result), 201

@maintenance_bp.route('/odometer', methods=['POST'])
def update_odometer():
    data = request.get_json() or {}
    vehicle_id = data.get('vehicle_id')
    new_mileage = data.get('mileage')

    if not vehicle_id or new_mileage is None:
        return jsonify({"success": False, "error": "vehicle_id and mileage are required"}), 400

    result = MaintenanceService.update_odometer_and_evaluate(int(vehicle_id), int(new_mileage))
    return jsonify(result)
