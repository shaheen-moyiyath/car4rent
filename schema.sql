-- ====================================================================
-- Car4Rent: A Web Based Car Rental System - MySQL Database Schema
-- Compatible with MySQL 5.7+ / MySQL 8.0+ / MariaDB
-- ====================================================================

CREATE DATABASE IF NOT EXISTS `car4rent_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `car4rent_db`;

-- 1. User Table
DROP TABLE IF EXISTS `AI_Recommendation`;
DROP TABLE IF EXISTS `Fine`;
DROP TABLE IF EXISTS `Maintenance`;
DROP TABLE IF EXISTS `GPS_Tracking`;
DROP TABLE IF EXISTS `Review`;
DROP TABLE IF EXISTS `Payment`;
DROP TABLE IF EXISTS `Booking`;
DROP TABLE IF EXISTS `Vehicle`;
DROP TABLE IF EXISTS `Vehicle_Category`;
DROP TABLE IF EXISTS `User`;

CREATE TABLE `User` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `role` VARCHAR(20) NOT NULL COMMENT 'Admin, Owner, Client',
    `email` VARCHAR(50) NOT NULL UNIQUE,
    `phone` VARCHAR(15) NOT NULL,
    `name` VARCHAR(50) NOT NULL,
    `password` VARCHAR(255) NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Vehicle Category Table
CREATE TABLE `Vehicle_Category` (
    `category_id` INT AUTO_INCREMENT PRIMARY KEY,
    `category_name` VARCHAR(50) NOT NULL UNIQUE,
    `description` TEXT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Vehicle Table
CREATE TABLE `Vehicle` (
    `vehicle_id` INT AUTO_INCREMENT PRIMARY KEY,
    `owner_id` INT NOT NULL,
    `category_id` INT NOT NULL,
    `vehicle_name` VARCHAR(50) NOT NULL,
    `location` VARCHAR(100) NOT NULL,
    `price_per_day` DECIMAL(10,2) NOT NULL,
    `availability` VARCHAR(20) NOT NULL DEFAULT 'Available' COMMENT 'Available, Booked, Maintenance',
    `mileage` INT NOT NULL DEFAULT 0,
    `vehicle_3d_view` TEXT NULL COMMENT 'JSON config or 3D GLTF asset reference',
    `gps_device_id` VARCHAR(50) NULL,
    `image_url` VARCHAR(255) NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_vehicle_owner` FOREIGN KEY (`owner_id`) REFERENCES `User` (`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_vehicle_category` FOREIGN KEY (`category_id`) REFERENCES `Vehicle_Category` (`category_id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Booking Table
CREATE TABLE `Booking` (
    `booking_id` INT AUTO_INCREMENT PRIMARY KEY,
    `client_id` INT NOT NULL,
    `vehicle_id` INT NOT NULL,
    `start_date` DATE NOT NULL,
    `end_date` DATE NOT NULL,
    `booking_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `total_amount` DECIMAL(10,2) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'Pending' COMMENT 'Pending, Approved, Rejected, Active, Completed, Cancelled',
    CONSTRAINT `fk_booking_client` FOREIGN KEY (`client_id`) REFERENCES `User` (`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_booking_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `Vehicle` (`vehicle_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Payment Table
CREATE TABLE `Payment` (
    `payment_id` INT AUTO_INCREMENT PRIMARY KEY,
    `booking_id` INT NOT NULL,
    `amount` DECIMAL(10,2) NOT NULL,
    `payment_method` VARCHAR(30) NOT NULL COMMENT 'Credit Card, Debit Card, UPI, PayPal, NetBanking',
    `transaction_id` VARCHAR(100) NOT NULL UNIQUE,
    `payment_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `payment_status` VARCHAR(20) NOT NULL DEFAULT 'Pending' COMMENT 'Pending, Completed, Failed, Refunded',
    CONSTRAINT `fk_payment_booking` FOREIGN KEY (`booking_id`) REFERENCES `Booking` (`booking_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Review Table
CREATE TABLE `Review` (
    `review_id` INT AUTO_INCREMENT PRIMARY KEY,
    `client_id` INT NOT NULL,
    `vehicle_id` INT NOT NULL,
    `booking_id` INT NOT NULL,
    `rating` INT NOT NULL CHECK (`rating` BETWEEN 1 AND 5),
    `review_text` TEXT NULL,
    `review_date` DATE NOT NULL,
    CONSTRAINT `fk_review_client` FOREIGN KEY (`client_id`) REFERENCES `User` (`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_review_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `Vehicle` (`vehicle_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_review_booking` FOREIGN KEY (`booking_id`) REFERENCES `Booking` (`booking_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. GPS Tracking Table
CREATE TABLE `GPS_Tracking` (
    `tracking_id` INT AUTO_INCREMENT PRIMARY KEY,
    `vehicle_id` INT NOT NULL,
    `latitude` DECIMAL(10,7) NOT NULL,
    `longitude` DECIMAL(10,7) NOT NULL,
    `tracked_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `speed` DECIMAL(6,2) NULL DEFAULT 0.00,
    CONSTRAINT `fk_gps_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `Vehicle` (`vehicle_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Maintenance Table
CREATE TABLE `Maintenance` (
    `maintenance_id` INT AUTO_INCREMENT PRIMARY KEY,
    `vehicle_id` INT NOT NULL,
    `service_type` VARCHAR(50) NOT NULL COMMENT 'Oil Change, Brake Inspection, Tire Rotation, Engine Tune-up, General Service',
    `service_date` DATE NOT NULL,
    `current_km` INT NOT NULL DEFAULT 0,
    `next_service_km` INT NOT NULL,
    `maintenance_status` VARCHAR(20) NOT NULL DEFAULT 'Pending' COMMENT 'Pending, In Progress, Completed, Overdue',
    CONSTRAINT `fk_maintenance_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `Vehicle` (`vehicle_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Fine Table
CREATE TABLE `Fine` (
    `fine_id` INT AUTO_INCREMENT PRIMARY KEY,
    `booking_id` INT NOT NULL,
    `fine_amount` DECIMAL(10,2) NOT NULL,
    `reason` VARCHAR(100) NOT NULL,
    `fine_date` DATE NOT NULL,
    `payment_status` VARCHAR(20) NOT NULL DEFAULT 'Unpaid' COMMENT 'Unpaid, Paid, Waived',
    CONSTRAINT `fk_fine_booking` FOREIGN KEY (`booking_id`) REFERENCES `Booking` (`booking_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. AI Recommendation Table
CREATE TABLE `AI_Recommendation` (
    `recommendation_id` INT AUTO_INCREMENT PRIMARY KEY,
    `client_id` INT NOT NULL,
    `vehicle_id` INT NOT NULL,
    `recommendation_score` DECIMAL(5,2) NOT NULL,
    `recommendation_reason` TEXT NULL,
    `generated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_ai_client` FOREIGN KEY (`client_id`) REFERENCES `User` (`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_ai_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `Vehicle` (`vehicle_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ====================================================================
-- SEED DATA (For initial platform setup & demonstration)
-- ====================================================================

-- 1. Insert Initial Users (Admin, Owners, Clients) - passwords hashed with SHA-256 for demo
-- (Pass: admin123, owner123, client123)
INSERT INTO `User` (`user_id`, `role`, `email`, `phone`, `name`, `password`) VALUES
(1, 'Admin', 'admin@car4rent.com', '+1-555-0100', 'System Administrator', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f'),
(2, 'Owner', 'alex.fleet@car4rent.com', '+1-555-0201', 'Alex Mercer (Apex Rentals)', '6a992d5529f459a44fee58c7332f6bb8f560dcf16650acb1d35a037992f80836'),
(3, 'Owner', 'sarah.drive@car4rent.com', '+1-555-0202', 'Sarah Connor (Prime Wheels)', '6a992d5529f459a44fee58c7332f6bb8f560dcf16650acb1d35a037992f80836'),
(4, 'Client', 'john.doe@gmail.com', '+1-555-0301', 'John Doe', 'd404559f602eab6fd602ac7680dacbfaadd13630335e951f097af3900e9de176'),
(5, 'Client', 'emily.watson@gmail.com', '+1-555-0302', 'Emily Watson', 'd404559f602eab6fd602ac7680dacbfaadd13630335e951f097af3900e9de176');

-- 2. Insert Vehicle Categories
INSERT INTO `Vehicle_Category` (`category_id`, `category_name`, `description`) VALUES
(1, 'Luxury Sedan', 'Premium executive vehicles offering superior comfort, elegance, and smooth driving performance.'),
(2, 'Electric & Hybrid', 'Eco-friendly and tech-forward electric and hybrid cars with maximum fuel economy and zero emissions.'),
(3, 'Compact SUV', 'Versatile and spacious utility vehicles perfect for family travel, city commuting, and weekend trips.'),
(4, 'Sports Coupe', 'High-performance sports cars designed for exhilarating speed, sharp handling, and dynamic style.'),
(5, 'Economy Hatchback', 'Budget-friendly, highly reliable, and compact city runabouts with easy parking and great mileage.');

-- 3. Insert Vehicles
INSERT INTO `Vehicle` (`vehicle_id`, `owner_id`, `category_id`, `vehicle_name`, `location`, `price_per_day`, `availability`, `mileage`, `vehicle_3d_view`, `gps_device_id`, `image_url`) VALUES
(1, 2, 2, 'Tesla Model 3 Performance', 'Downtown Metro Station, Bay 4', 95.00, 'Available', 24800, '{"color":"#c51111","modelType":"sedan","wheelStyle":"sport","wireframe":false,"metallic":0.8}', 'GPS-TSL-301', 'https://images.unsplash.com/photo-1560958089-b8a1929cea89?auto=format&fit=crop&w=800&q=80'),
(2, 2, 1, 'Mercedes-Benz E-Class AMG', 'Airport Terminal 2 Luxury Lane', 140.00, 'Available', 48200, '{"color":"#1a202c","modelType":"sedan","wheelStyle":"luxury","wireframe":false,"metallic":0.9}', 'GPS-MBZ-502', 'https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=800&q=80'),
(3, 3, 3, 'BMW X5 xDrive40i', 'Uptown Business Center', 130.00, 'Available', 35100, '{"color":"#1e3a8a","modelType":"suv","wheelStyle":"offroad","wireframe":false,"metallic":0.7}', 'GPS-BMW-803', 'https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=800&q=80'),
(4, 3, 4, 'Porsche 911 Carrera', 'Marina Bay Resort Hub', 220.00, 'Available', 19400, '{"color":"#eab308","modelType":"coupe","wheelStyle":"sport","wireframe":false,"metallic":0.95}', 'GPS-POR-911', 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=800&q=80'),
(5, 2, 5, 'Toyota Corolla Hybrid', 'Westside Central Plaza', 45.00, 'Available', 59800, '{"color":"#4b5563","modelType":"hatchback","wheelStyle":"standard","wireframe":false,"metallic":0.5}', 'GPS-TOY-204', 'https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb?auto=format&fit=crop&w=800&q=80'),
(6, 3, 3, 'Hyundai Tucson Limited', 'North Hills Shopping Hub', 65.00, 'Available', 31200, '{"color":"#0f766e","modelType":"suv","wheelStyle":"standard","wireframe":false,"metallic":0.6}', 'GPS-HYU-707', 'https://images.unsplash.com/photo-1583121274602-3e2820c69888?auto=format&fit=crop&w=800&q=80');

-- 4. Insert Initial Bookings
INSERT INTO `Booking` (`booking_id`, `client_id`, `vehicle_id`, `start_date`, `end_date`, `booking_date`, `total_amount`, `status`) VALUES
(1, 4, 1, '2026-09-20', '2026-09-24', '2026-09-18 10:30:00', 380.00, 'Completed'),
(2, 4, 3, '2026-09-28', '2026-10-02', '2026-09-26 14:15:00', 520.00, 'Completed'),
(3, 5, 2, '2026-10-01', '2026-10-06', '2026-09-30 09:00:00', 700.00, 'Active'),
(4, 4, 4, '2026-10-04', '2026-10-07', '2026-10-03 16:40:00', 660.00, 'Active');

-- 5. Insert Payments
INSERT INTO `Payment` (`payment_id`, `booking_id`, `amount`, `payment_method`, `transaction_id`, `payment_date`, `payment_status`) VALUES
(1, 1, 380.00, 'Credit Card', 'TXN-C4R-88291039', '2026-09-18 10:35:00', 'Completed'),
(2, 2, 520.00, 'UPI', 'TXN-C4R-99381021', '2026-09-26 14:20:00', 'Completed'),
(3, 3, 700.00, 'Debit Card', 'TXN-C4R-10294820', '2026-09-30 09:05:00', 'Completed'),
(4, 4, 660.00, 'Credit Card', 'TXN-C4R-77182904', '2026-10-03 16:45:00', 'Completed');

-- 6. Insert Reviews
INSERT INTO `Review` (`review_id`, `client_id`, `vehicle_id`, `booking_id`, `rating`, `review_text`, `review_date`) VALUES
(1, 4, 1, 1, 5, 'Exceptional experience with the Tesla Model 3. Full battery on pickup, immaculate interior, and super smooth acceleration!', '2026-09-25'),
(2, 4, 3, 2, 4, 'The BMW X5 was luxurious and roomy for our weekend family trip. Easy pickup and drop off procedure.', '2026-10-03');

-- 7. Insert GPS Tracking Real-Time Telemetry
INSERT INTO `GPS_Tracking` (`tracking_id`, `vehicle_id`, `latitude`, `longitude`, `tracked_at`, `speed`) VALUES
(1, 1, 37.774929, -122.419416, NOW() - INTERVAL 15 MINUTE, 45.5),
(2, 1, 37.778210, -122.415300, NOW() - INTERVAL 10 MINUTE, 52.0),
(3, 1, 37.781500, -122.410200, NOW() - INTERVAL 5 MINUTE, 38.2),
(4, 1, 37.785834, -122.406417, NOW(), 0.0),
(5, 2, 37.783333, -122.416667, NOW(), 62.4),
(6, 3, 37.769000, -122.446000, NOW(), 48.0),
(7, 4, 37.808000, -122.417000, NOW(), 55.8);

-- 8. Insert Maintenance Records & Odometer Alerts
INSERT INTO `Maintenance` (`maintenance_id`, `vehicle_id`, `service_type`, `service_date`, `current_km`, `next_service_km`, `maintenance_status`) VALUES
(1, 1, 'Tire Rotation & Battery Diagnostic', '2026-08-15', 24800, 30000, 'Completed'),
(2, 2, 'Brake Pad Replacement & Oil Change', '2026-09-01', 48200, 50000, 'Pending'),
(3, 5, 'Full Engine Tune-up', '2026-07-20', 59800, 60000, 'Overdue');

-- 9. Insert Fines Sample
INSERT INTO `Fine` (`fine_id`, `booking_id`, `fine_amount`, `reason`, `fine_date`, `payment_status`) VALUES
(1, 1, 50.00, 'Late return overdue by 3 hours past scheduled drop-off', '2026-09-24', 'Paid');

-- 10. Insert AI Recommendations Seed
INSERT INTO `AI_Recommendation` (`recommendation_id`, `client_id`, `vehicle_id`, `recommendation_score`, `recommendation_reason`, `generated_at`) VALUES
(1, 4, 1, 96.50, 'Matched client high rating preference for Electric Vehicles within $80-$120/day budget range.', NOW()),
(2, 4, 3, 89.20, 'Recommended based on past completed SUV booking history and verified 4.8/5 owner rating.', NOW());
