import os
import sqlite3
import pymysql
import hashlib
from config import Config

def hash_password(password: str) -> str:
    """Hash password using SHA-256 for secure storage."""
    if not password:
        return ""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

class Database:
    _engine = None

    @classmethod
    def get_connection(cls):
        """
        Attempts to connect to MySQL based on Config.
        If MySQL is unavailable or offline, gracefully falls back to SQLite
        with zero manual setup required.
        """
        try:
            conn = pymysql.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            cls._engine = 'mysql'
            return conn, 'mysql'
        except Exception:
            # Fallback to SQLite
            cls._engine = 'sqlite'
            conn = sqlite3.connect(Config.SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn, 'sqlite'

    @classmethod
    def execute_query(cls, sql: str, params: tuple = ()):
        """Execute a query and return results or last row ID."""
        conn, engine = cls.get_connection()
        cursor = conn.cursor()
        
        # Normalize SQL parameter placeholders between MySQL (%s) and SQLite (?)
        if engine == 'sqlite':
            sql = sql.replace('%s', '?')
        else:
            sql = sql.replace('?', '%s')
            
        try:
            cursor.execute(sql, params)
            if sql.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE')):
                if engine == 'sqlite':
                    rows = cursor.fetchall()
                    result = [dict(row) for row in rows]
                else:
                    result = cursor.fetchall()
                return result
            else:
                if engine == 'sqlite':
                    conn.commit()
                last_id = cursor.lastrowid
                row_count = cursor.rowcount
                return {'last_id': last_id, 'affected_rows': row_count}
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def init_sqlite_db(cls):
        """Initialize SQLite database with full schema and seed data if not existing."""
        conn = sqlite3.connect(Config.SQLITE_DB_PATH)
        cursor = conn.cursor()
        
        cursor.executescript('''
        CREATE TABLE IF NOT EXISTS User (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS Vehicle_Category (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS Vehicle (
            vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            vehicle_name TEXT NOT NULL,
            location TEXT NOT NULL,
            price_per_day REAL NOT NULL,
            availability TEXT NOT NULL DEFAULT 'Available',
            mileage INTEGER NOT NULL DEFAULT 0,
            vehicle_3d_view TEXT,
            gps_device_id TEXT,
            image_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES User(user_id),
            FOREIGN KEY (category_id) REFERENCES Vehicle_Category(category_id)
        );

        CREATE TABLE IF NOT EXISTS Booking (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            vehicle_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            FOREIGN KEY (client_id) REFERENCES User(user_id),
            FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
        );

        CREATE TABLE IF NOT EXISTS Payment (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            transaction_id TEXT NOT NULL UNIQUE,
            payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            payment_status TEXT NOT NULL DEFAULT 'Pending',
            FOREIGN KEY (booking_id) REFERENCES Booking(booking_id)
        );

        CREATE TABLE IF NOT EXISTS Review (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            vehicle_id INTEGER NOT NULL,
            booking_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            review_text TEXT,
            review_date DATE DEFAULT (DATE('now')),
            FOREIGN KEY (client_id) REFERENCES User(user_id),
            FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id),
            FOREIGN KEY (booking_id) REFERENCES Booking(booking_id)
        );

        CREATE TABLE IF NOT EXISTS GPS_Tracking (
            tracking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            tracked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            speed REAL DEFAULT 0.0,
            FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
        );

        CREATE TABLE IF NOT EXISTS Maintenance (
            maintenance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            service_type TEXT NOT NULL,
            service_date TEXT NOT NULL,
            current_km INTEGER NOT NULL DEFAULT 0,
            next_service_km INTEGER NOT NULL,
            maintenance_status TEXT NOT NULL DEFAULT 'Pending',
            FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
        );

        CREATE TABLE IF NOT EXISTS Fine (
            fine_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            fine_amount REAL NOT NULL,
            reason TEXT NOT NULL,
            fine_date TEXT NOT NULL,
            payment_status TEXT NOT NULL DEFAULT 'Unpaid',
            FOREIGN KEY (booking_id) REFERENCES Booking(booking_id)
        );

        CREATE TABLE IF NOT EXISTS AI_Recommendation (
            recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            vehicle_id INTEGER NOT NULL,
            recommendation_score REAL NOT NULL,
            recommendation_reason TEXT,
            generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES User(user_id),
            FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
        );
        ''')
        
        # Check if users already seeded
        cursor.execute("SELECT COUNT(*) FROM User")
        count = cursor.fetchone()[0]
        if count == 0:
            # Seed users (Passwords: admin123, owner123, client123)
            cursor.executescript('''
            INSERT INTO User (user_id, role, email, phone, name, password) VALUES
            (1, 'Admin', 'admin@car4rent.com', '+1-555-0100', 'System Administrator', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f'),
            (2, 'Owner', 'alex.fleet@car4rent.com', '+1-555-0201', 'Alex Mercer (Apex Fleet)', '6a992d5529f459a44fee58c7332f6bb8f560dcf16650acb1d35a037992f80836'),
            (3, 'Owner', 'sarah.drive@car4rent.com', '+1-555-0202', 'Sarah Connor (Prime Wheels)', '6a992d5529f459a44fee58c7332f6bb8f560dcf16650acb1d35a037992f80836'),
            (4, 'Client', 'john.doe@gmail.com', '+1-555-0301', 'John Doe', 'd404559f602eab6fd602ac7680dacbfaadd13630335e951f097af3900e9de176'),
            (5, 'Client', 'emily.watson@gmail.com', '+1-555-0302', 'Emily Watson', 'd404559f602eab6fd602ac7680dacbfaadd13630335e951f097af3900e9de176');

            INSERT INTO Vehicle_Category (category_id, category_name, description) VALUES
            (1, 'Luxury Sedan', 'Premium executive vehicles offering superior comfort, elegance, and smooth driving performance.'),
            (2, 'Electric & Hybrid', 'Eco-friendly and tech-forward electric and hybrid cars with maximum fuel economy and zero emissions.'),
            (3, 'Compact SUV', 'Versatile and spacious utility vehicles perfect for family travel, city commuting, and weekend trips.'),
            (4, 'Sports Coupe', 'High-performance sports cars designed for exhilarating speed, sharp handling, and dynamic style.'),
            (5, 'Economy Hatchback', 'Budget-friendly, highly reliable, and compact city runabouts with easy parking and great mileage.');

            INSERT INTO Vehicle (vehicle_id, owner_id, category_id, vehicle_name, location, price_per_day, availability, mileage, vehicle_3d_view, gps_device_id, image_url) VALUES
            (1, 2, 2, 'Tesla Model 3 Performance', 'Downtown Metro Station, Bay 4', 95.00, 'Available', 24800, '{"color":"#c51111","modelType":"sedan","wheelStyle":"sport","metallic":0.8,"roughness":0.2}', 'GPS-TSL-301', 'https://images.unsplash.com/photo-1560958089-b8a1929cea89?auto=format&fit=crop&w=800&q=80'),
            (2, 2, 1, 'Mercedes-Benz E-Class AMG', 'Airport Terminal 2 Luxury Lane', 140.00, 'Available', 48200, '{"color":"#1a202c","modelType":"sedan","wheelStyle":"luxury","metallic":0.9,"roughness":0.1}', 'GPS-MBZ-502', 'https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=800&q=80'),
            (3, 3, 3, 'BMW X5 xDrive40i', 'Uptown Business Center', 130.00, 'Available', 35100, '{"color":"#1e3a8a","modelType":"suv","wheelStyle":"offroad","metallic":0.7,"roughness":0.3}', 'GPS-BMW-803', 'https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=800&q=80'),
            (4, 3, 4, 'Porsche 911 Carrera', 'Marina Bay Resort Hub', 220.00, 'Available', 19400, '{"color":"#eab308","modelType":"coupe","wheelStyle":"sport","metallic":0.95,"roughness":0.1}', 'GPS-POR-911', 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=800&q=80'),
            (5, 2, 5, 'Toyota Corolla Hybrid', 'Westside Central Plaza', 45.00, 'Available', 59800, '{"color":"#4b5563","modelType":"hatchback","wheelStyle":"standard","metallic":0.5,"roughness":0.4}', 'GPS-TOY-204', 'https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb?auto=format&fit=crop&w=800&q=80'),
            (6, 3, 3, 'Hyundai Tucson Limited', 'North Hills Shopping Hub', 65.00, 'Available', 31200, '{"color":"#0f766e","modelType":"suv","wheelStyle":"standard","metallic":0.6,"roughness":0.3}', 'GPS-HYU-707', 'https://images.unsplash.com/photo-1583121274602-3e2820c69888?auto=format&fit=crop&w=800&q=80');

            INSERT INTO Booking (booking_id, client_id, vehicle_id, start_date, end_date, booking_date, total_amount, status) VALUES
            (1, 4, 1, '2026-09-20', '2026-09-24', '2026-09-18 10:30:00', 380.00, 'Completed'),
            (2, 4, 3, '2026-09-28', '2026-10-02', '2026-09-26 14:15:00', 520.00, 'Completed'),
            (3, 5, 2, '2026-10-01', '2026-10-06', '2026-09-30 09:00:00', 700.00, 'Active'),
            (4, 4, 4, '2026-10-04', '2026-10-07', '2026-10-03 16:40:00', 660.00, 'Active');

            INSERT INTO Payment (payment_id, booking_id, amount, payment_method, transaction_id, payment_date, payment_status) VALUES
            (1, 1, 380.00, 'Credit Card', 'TXN-C4R-88291039', '2026-09-18 10:35:00', 'Completed'),
            (2, 2, 520.00, 'UPI', 'TXN-C4R-99381021', '2026-09-26 14:20:00', 'Completed'),
            (3, 3, 700.00, 'Debit Card', 'TXN-C4R-10294820', '2026-09-30 09:05:00', 'Completed'),
            (4, 4, 660.00, 'Credit Card', 'TXN-C4R-77182904', '2026-10-03 16:45:00', 'Completed');

            INSERT INTO Review (review_id, client_id, vehicle_id, booking_id, rating, review_text, review_date) VALUES
            (1, 4, 1, 1, 5, 'Exceptional experience with the Tesla Model 3. Full battery on pickup, immaculate interior, and super smooth acceleration!', '2026-09-25'),
            (2, 4, 3, 2, 4, 'The BMW X5 was luxurious and roomy for our weekend family trip. Easy pickup and drop off procedure.', '2026-10-03');

            INSERT INTO GPS_Tracking (tracking_id, vehicle_id, latitude, longitude, tracked_at, speed) VALUES
            (1, 1, 37.774929, -122.419416, DATETIME('now', '-15 minutes'), 45.5),
            (2, 1, 37.778210, -122.415300, DATETIME('now', '-10 minutes'), 52.0),
            (3, 1, 37.781500, -122.410200, DATETIME('now', '-5 minutes'), 38.2),
            (4, 1, 37.785834, -122.406417, DATETIME('now'), 0.0),
            (5, 2, 37.783333, -122.416667, DATETIME('now'), 62.4),
            (6, 3, 37.769000, -122.446000, DATETIME('now'), 48.0),
            (7, 4, 37.808000, -122.417000, DATETIME('now'), 55.8);

            INSERT INTO Maintenance (maintenance_id, vehicle_id, service_type, service_date, current_km, next_service_km, maintenance_status) VALUES
            (1, 1, 'Tire Rotation & Battery Diagnostic', '2026-08-15', 24800, 30000, 'Completed'),
            (2, 2, 'Brake Pad Replacement & Oil Change', '2026-09-01', 48200, 50000, 'Pending'),
            (3, 5, 'Full Engine Tune-up', '2026-07-20', 59800, 60000, 'Overdue');

            INSERT INTO Fine (fine_id, booking_id, fine_amount, reason, fine_date, payment_status) VALUES
            (1, 1, 50.00, 'Late return overdue by 3 hours past scheduled drop-off', '2026-09-24', 'Paid');

            INSERT INTO AI_Recommendation (recommendation_id, client_id, vehicle_id, recommendation_score, recommendation_reason, generated_at) VALUES
            (1, 4, 1, 96.50, 'Matched client high rating preference for Electric Vehicles within $80-$120/day budget range.', DATETIME('now')),
            (2, 4, 3, 89.20, 'Recommended based on past completed SUV booking history and verified 4.8/5 owner rating.', DATETIME('now'));
            ''')
        
        conn.commit()
        conn.close()
