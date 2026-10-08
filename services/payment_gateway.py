import uuid
import hashlib
import time
from database import Database
from config import Config

class PaymentGatewayService:
    """
    Digital Payment Gateway Service:
    Provides mock integration for credit/debit card, UPI, NetBanking, and digital wallets.
    Generates secure transaction tokens, computes signature hashes, and updates Payment & Booking records.
    """

    @classmethod
    def generate_transaction_signature(cls, booking_id: int, amount: float, timestamp: int) -> str:
        """Generates a cryptographic signature token for payment verification."""
        payload = f"{booking_id}-{amount:.2f}-{timestamp}-{Config.SECRET_KEY}"
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    @classmethod
    def process_payment(cls, booking_id: int, amount: float, payment_method: str) -> dict:
        """
        Executes payment transaction for a booking.
        1. Validates booking exists.
        2. Creates unique transaction ID.
        3. Inserts Payment record with 'Completed' status.
        4. Updates Booking status to 'Active'.
        5. Updates Vehicle availability to 'Booked'.
        """
        # Validate booking
        bookings = Database.execute_query(
            "SELECT * FROM Booking WHERE booking_id = %s",
            (booking_id,)
        )
        if not bookings:
            return {"success": False, "error": "Invalid booking ID"}
        
        booking = bookings[0]
        vehicle_id = booking['vehicle_id']
        
        # Generate transaction identifier
        timestamp = int(time.time())
        txn_id = f"TXN-C4R-{uuid.uuid4().hex[:10].upper()}"
        signature = cls.generate_transaction_signature(booking_id, amount, timestamp)
        
        # Insert Payment
        insert_payment_sql = """
            INSERT INTO Payment (booking_id, amount, payment_method, transaction_id, payment_date, payment_status)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, 'Completed')
        """
        pay_res = Database.execute_query(insert_payment_sql, (
            booking_id,
            amount,
            payment_method,
            txn_id
        ))
        
        # Update Booking to Active
        Database.execute_query(
            "UPDATE Booking SET status = 'Active' WHERE booking_id = %s",
            (booking_id,)
        )
        
        # Update Vehicle to Booked
        Database.execute_query(
            "UPDATE Vehicle SET availability = 'Booked' WHERE vehicle_id = %s",
            (vehicle_id,)
        )
        
        return {
            "success": True,
            "payment_id": pay_res.get('last_id'),
            "booking_id": booking_id,
            "amount": amount,
            "payment_method": payment_method,
            "transaction_id": txn_id,
            "signature": signature,
            "payment_status": "Completed",
            "message": "Payment verified and processed successfully. Vehicle is now booked."
        }
