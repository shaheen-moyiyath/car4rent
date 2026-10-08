from database import Database
from datetime import datetime
import math
import random

class GPSTrackingService:
    """
    Open-source GPS Telemetry and Tracking Service:
    Provides real-time vehicle positioning, route history logging, speed monitoring,
    and simulated live telemetry updates for connected IoT/GPS modules.
    """

    @classmethod
    def record_gps_telemetry(cls, vehicle_id: int, latitude: float, longitude: float, speed: float = 0.0) -> dict:
        """Records a new GPS point for a vehicle."""
        sql = """
            INSERT INTO GPS_Tracking (vehicle_id, latitude, longitude, tracked_at, speed)
            VALUES (%s, %s, %s, %s, %s)
        """
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result = Database.execute_query(sql, (vehicle_id, latitude, longitude, now_str, speed))
        
        return {
            "success": True,
            "tracking_id": result.get('last_id'),
            "vehicle_id": vehicle_id,
            "latitude": latitude,
            "longitude": longitude,
            "speed": speed,
            "tracked_at": now_str
        }

    @classmethod
    def get_latest_position(cls, vehicle_id: int) -> dict:
        """Retrieves the most recent GPS fix for a vehicle."""
        sql = """
            SELECT g.*, v.vehicle_name, v.gps_device_id, v.availability
            FROM GPS_Tracking g
            JOIN Vehicle v ON g.vehicle_id = v.vehicle_id
            WHERE g.vehicle_id = %s
            ORDER BY g.tracking_id DESC
            LIMIT 1
        """
        rows = Database.execute_query(sql, (vehicle_id,))
        if rows:
            pos = rows[0]
            return {
                "success": True,
                "tracking_id": pos['tracking_id'],
                "vehicle_id": pos['vehicle_id'],
                "vehicle_name": pos['vehicle_name'],
                "gps_device_id": pos['gps_device_id'],
                "latitude": float(pos['latitude']),
                "longitude": float(pos['longitude']),
                "speed": float(pos['speed']),
                "tracked_at": str(pos['tracked_at']),
                "status": pos['availability']
            }
        
        # Fallback coordinate if no telemetry recorded yet
        return {
            "success": True,
            "vehicle_id": vehicle_id,
            "latitude": 37.7749,
            "longitude": -122.4194,
            "speed": 0.0,
            "tracked_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "status": "Available"
        }

    @classmethod
    def get_vehicle_route_history(cls, vehicle_id: int, limit: int = 50) -> list:
        """Fetches historical waypoints for route reconstruction."""
        sql = f"""
            SELECT tracking_id, vehicle_id, latitude, longitude, tracked_at, speed
            FROM GPS_Tracking
            WHERE vehicle_id = %s
            ORDER BY tracking_id ASC
            LIMIT {int(limit)}
        """
        rows = Database.execute_query(sql, (vehicle_id,))
        history = []
        for r in rows:
            history.append({
                "tracking_id": r['tracking_id'],
                "latitude": float(r['latitude']),
                "longitude": float(r['longitude']),
                "speed": float(r['speed']),
                "tracked_at": str(r['tracked_at'])
            })
        return history

    @classmethod
    def get_owner_fleet_live_positions(cls, owner_id: int) -> list:
        """Fetches the latest positions of all vehicles belonging to a specific owner."""
        sql = """
            SELECT v.vehicle_id, v.vehicle_name, v.location, v.gps_device_id, v.availability,
                   g.latitude, g.longitude, g.speed, g.tracked_at
            FROM Vehicle v
            LEFT JOIN GPS_Tracking g ON g.tracking_id = (
                SELECT tracking_id FROM GPS_Tracking 
                WHERE vehicle_id = v.vehicle_id 
                ORDER BY tracking_id DESC LIMIT 1
            )
            WHERE v.owner_id = %s
        """
        rows = Database.execute_query(sql, (owner_id,))
        fleet = []
        for r in rows:
            fleet.append({
                "vehicle_id": r['vehicle_id'],
                "vehicle_name": r['vehicle_name'],
                "location": r['location'],
                "gps_device_id": r['gps_device_id'] or 'N/A',
                "availability": r['availability'],
                "latitude": float(r['latitude']) if r['latitude'] is not None else 37.7749,
                "longitude": float(r['longitude']) if r['longitude'] is not None else -122.4194,
                "speed": float(r['speed']) if r['speed'] is not None else 0.0,
                "tracked_at": str(r['tracked_at']) if r['tracked_at'] else 'Live'
            })
        return fleet

    @classmethod
    def simulate_telemetry_step(cls, vehicle_id: int) -> dict:
        """
        Simulates slight movement along a realistic driving vector for real-time demonstration.
        """
        latest = cls.get_latest_position(vehicle_id)
        current_lat = latest['latitude']
        current_lng = latest['longitude']
        
        # Add slight delta simulating driving at ~40-60 km/h
        delta_lat = (random.random() - 0.5) * 0.003
        delta_lng = (random.random() - 0.5) * 0.003
        new_lat = current_lat + delta_lat
        new_lng = current_lng + delta_lng
        speed = round(random.uniform(30.0, 75.0), 1)
        
        return cls.record_gps_telemetry(vehicle_id, new_lat, new_lng, speed)
