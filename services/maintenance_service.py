from config import Config
from database import Database
from datetime import date

class MaintenanceService:
    """
    Kilometer-based Maintenance Alert Service:
    Monitors vehicle odometer readings against scheduled service intervals
    and triggers alerts when current_km >= next_service_km or approaching threshold.
    """

    @classmethod
    def check_vehicle_maintenance_status(cls, vehicle_id: int) -> dict:
        """
        Evaluates the current mileage of a vehicle against its latest maintenance schedule.
        Status classifications:
        - 'OVERDUE': current_km >= next_service_km
        - 'WARNING': (next_service_km - current_km) <= Config.MAINTENANCE_WARNING_KM_THRESHOLD
        - 'OK': healthy operating condition
        """
        # Fetch vehicle and latest maintenance record
        vehicle = Database.execute_query(
            "SELECT vehicle_id, vehicle_name, mileage, owner_id FROM Vehicle WHERE vehicle_id = %s",
            (vehicle_id,)
        )
        if not vehicle:
            return {"success": False, "error": "Vehicle not found"}
        
        car = vehicle[0]
        current_km = int(car['mileage'])
        
        maintenance_records = Database.execute_query(
            """
            SELECT * FROM Maintenance 
            WHERE vehicle_id = %s 
            ORDER BY maintenance_id DESC LIMIT 1
            """,
            (vehicle_id,)
        )
        
        if not maintenance_records:
            # Default first service threshold if none recorded
            next_service_km = current_km + 5000
            alert_status = "OK"
            remaining_km = 5000
            record_id = None
        else:
            rec = maintenance_records[0]
            record_id = rec['maintenance_id']
            next_service_km = int(rec['next_service_km'])
            remaining_km = next_service_km - current_km
            
            if current_km >= next_service_km:
                alert_status = "OVERDUE"
                if rec['maintenance_status'] != 'Overdue':
                    # Update status in DB
                    Database.execute_query(
                        "UPDATE Maintenance SET maintenance_status = 'Overdue' WHERE maintenance_id = %s",
                        (record_id,)
                    )
            elif remaining_km <= Config.MAINTENANCE_WARNING_KM_THRESHOLD:
                alert_status = "WARNING"
            else:
                alert_status = "OK"
                
        return {
            "success": True,
            "vehicle_id": vehicle_id,
            "vehicle_name": car['vehicle_name'],
            "current_km": current_km,
            "next_service_km": next_service_km,
            "remaining_km": remaining_km,
            "alert_status": alert_status,
            "is_alert_triggered": alert_status in ["OVERDUE", "WARNING"],
            "maintenance_id": record_id
        }

    @classmethod
    def update_odometer_and_evaluate(cls, vehicle_id: int, new_mileage: int) -> dict:
        """
        Updates the vehicle's mileage and checks if a maintenance alert should be triggered.
        """
        Database.execute_query(
            "UPDATE Vehicle SET mileage = %s WHERE vehicle_id = %s",
            (new_mileage, vehicle_id)
        )
        
        # Also update current_km on latest active maintenance record
        Database.execute_query(
            """
            UPDATE Maintenance 
            SET current_km = %s 
            WHERE vehicle_id = %s AND maintenance_status IN ('Pending', 'Overdue')
            """,
            (new_mileage, vehicle_id)
        )
        
        return cls.check_vehicle_maintenance_status(vehicle_id)

    @classmethod
    def log_maintenance_service(cls, vehicle_id: int, service_type: str, current_km: int, next_service_interval_km: int = 10000) -> dict:
        """
        Logs a newly performed service and sets the next service odometer threshold.
        """
        service_date = date.today().strftime('%Y-%m-%d')
        next_service_km = current_km + next_service_interval_km
        
        # Mark previous pending services as completed
        Database.execute_query(
            "UPDATE Maintenance SET maintenance_status = 'Completed' WHERE vehicle_id = %s AND maintenance_status != 'Completed'",
            (vehicle_id,)
        )
        
        # Insert new maintenance milestone
        insert_sql = """
            INSERT INTO Maintenance (vehicle_id, service_type, service_date, current_km, next_service_km, maintenance_status)
            VALUES (%s, %s, %s, %s, %s, 'Pending')
        """
        res = Database.execute_query(insert_sql, (vehicle_id, service_type, service_date, current_km, next_service_km))
        
        return {
            "success": True,
            "maintenance_id": res.get('last_id'),
            "vehicle_id": vehicle_id,
            "service_type": service_type,
            "service_date": service_date,
            "current_km": current_km,
            "next_service_km": next_service_km,
            "maintenance_status": "Pending"
        }

    @classmethod
    def get_owner_fleet_alerts(cls, owner_id: int) -> list:
        """
        Returns all maintenance alerts for an owner's entire fleet.
        """
        vehicles = Database.execute_query(
            "SELECT vehicle_id FROM Vehicle WHERE owner_id = %s",
            (owner_id,)
        )
        fleet_status = []
        for v in vehicles:
            status = cls.check_vehicle_maintenance_status(v['vehicle_id'])
            if status.get("success"):
                fleet_status.append(status)
        return fleet_status
