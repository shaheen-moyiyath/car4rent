from datetime import datetime, date
from config import Config
from database import Database

class FineCalculatorService:
    """
    Automated Fine Calculation Service:
    Calculates overdue penalty fees automatically when a client returns a vehicle past `end_date`
    or when checking overdue bookings.
    """

    @classmethod
    def calculate_overdue_fine(cls, booking_id: int, return_date_str: str = None) -> dict:
        """
        Calculates overdue fine for a given booking.
        Formula:
        Overdue Days = max(0, return_date - end_date)
        Overdue Fine = BASE_LATE_FEE + (overdue_days * price_per_day * DAILY_OVERDUE_RATE_MULTIPLIER)
        """
        # Fetch booking details along with vehicle price
        sql = """
            SELECT b.booking_id, b.client_id, b.vehicle_id, b.start_date, b.end_date, b.status,
                   v.vehicle_name, v.price_per_day
            FROM Booking b
            JOIN Vehicle v ON b.vehicle_id = v.vehicle_id
            WHERE b.booking_id = %s
        """
        bookings = Database.execute_query(sql, (booking_id,))
        if not bookings:
            return {"success": False, "error": "Booking not found"}
        
        booking = bookings[0]
        
        # Parse dates
        end_date = datetime.strptime(str(booking['end_date']), '%Y-%m-%d').date()
        if return_date_str:
            return_date = datetime.strptime(str(return_date_str), '%Y-%m-%d').date()
        else:
            return_date = date.today()
            
        overdue_days = (return_date - end_date).days
        
        if overdue_days <= 0:
            return {
                "success": True,
                "is_overdue": False,
                "overdue_days": 0,
                "fine_amount": 0.0,
                "reason": "Vehicle returned on time"
            }
            
        price_per_day = float(booking['price_per_day'])
        fine_amount = round(
            Config.BASE_LATE_FEE + (overdue_days * price_per_day * Config.DAILY_OVERDUE_RATE_MULTIPLIER),
            2
        )
        reason = f"Late return: {overdue_days} day(s) overdue past agreed return date ({end_date})."
        
        return {
            "success": True,
            "is_overdue": True,
            "overdue_days": overdue_days,
            "daily_rate": price_per_day,
            "multiplier": Config.DAILY_OVERDUE_RATE_MULTIPLIER,
            "base_fee": Config.BASE_LATE_FEE,
            "fine_amount": fine_amount,
            "reason": reason,
            "end_date": str(end_date),
            "actual_date": str(return_date)
        }

    @classmethod
    def apply_and_record_fine(cls, booking_id: int, return_date_str: str = None) -> dict:
        """
        Calculates and persists a fine record in the Fine table if overdue.
        """
        fine_data = cls.calculate_overdue_fine(booking_id, return_date_str)
        if not fine_data.get("success") or not fine_data.get("is_overdue"):
            return fine_data
        
        # Check if fine already recorded for this booking
        existing = Database.execute_query("SELECT * FROM Fine WHERE booking_id = %s", (booking_id,))
        if existing:
            return {
                "success": True,
                "fine_id": existing[0]['fine_id'],
                "fine_amount": float(existing[0]['fine_amount']),
                "reason": existing[0]['reason'],
                "payment_status": existing[0]['payment_status'],
                "already_existed": True
            }
        
        fine_date = return_date_str if return_date_str else date.today().strftime('%Y-%m-%d')
        insert_sql = """
            INSERT INTO Fine (booking_id, fine_amount, reason, fine_date, payment_status)
            VALUES (%s, %s, %s, %s, 'Unpaid')
        """
        result = Database.execute_query(insert_sql, (
            booking_id,
            fine_data['fine_amount'],
            fine_data['reason'],
            fine_date
        ))
        
        return {
            "success": True,
            "fine_id": result.get('last_id'),
            "fine_amount": fine_data['fine_amount'],
            "reason": fine_data['reason'],
            "payment_status": "Unpaid",
            "overdue_days": fine_data['overdue_days']
        }
