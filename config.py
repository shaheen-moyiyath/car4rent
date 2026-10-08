import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'car4rent-super-secret-jwt-key-2026')
    
    # MySQL Database Configurations
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'car4rent_db')
    
    # SQLite Fallback path (use /tmp on serverless platforms like Vercel)
    if os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        SQLITE_DB_PATH = '/tmp/car4rent.sqlite3'
    else:
        SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'car4rent.sqlite3')

    
    # Fine Calculation Parameters
    DAILY_OVERDUE_RATE_MULTIPLIER = float(os.environ.get('DAILY_OVERDUE_RATE_MULTIPLIER', 1.5)) # 1.5x daily rent
    BASE_LATE_FEE = float(os.environ.get('BASE_LATE_FEE', 25.0)) # Flat penalty fee
    
    # Maintenance Alert Thresholds
    MAINTENANCE_WARNING_KM_THRESHOLD = int(os.environ.get('MAINTENANCE_WARNING_KM_THRESHOLD', 500)) # Alert within 500km of next service
    
    # Payment Gateway Mock Settings
    PAYMENT_GATEWAY_CURRENCY = 'USD'
    PAYMENT_GATEWAY_MERCHANT_NAME = 'Car4Rent Global Mobility'
