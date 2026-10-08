# Car4Rent: Web-Based Multi-Owner Car Rental Platform

**Car4Rent** is a full-stack, AI-powered multi-owner car rental platform designed to modernize vehicle rental operations. It connects vehicle fleet owners, clients, and platform administrators within a unified digital ecosystem featuring real-time GPS tracking, automated overdue fine calculation, kilometer-based maintenance scheduling, interactive 3D WebGL vehicle inspection, and AI recommendation engines.

---

## 🚀 Key Features

### 1. Multi-Owner Fleet Management
- **Owner Dashboard**: Add, update, and manage vehicle listings, daily pricing, and availability.
- **Real-Time Open-Source GPS Tracking**: Live telemetry map powered by Leaflet.js and OpenStreetMap with speed radar, live coordinates, and route waypoints.
- **Kilometer-Based Maintenance Alerts**: Automated odometer tracking that triggers warnings and overdue service flags when `current_km >= next_service_km`.
- **Automated Fine Calculation**: Auto-assesses late return penalty fees based on overdue duration.

### 2. Client Experience & AI Personalization
- **AI Recommendation Engine**: Hybrid score-based collaborative filtering model computing personalized vehicle rankings based on budget affinity, category preferences, and verified customer ratings.
- **Interactive 3D WebGL Vehicle Inspector**: Built with Three.js featuring 360° orbit rotation, zoom, custom paint color picker, and chassis wireframe mode.
- **Seamless Booking & Payment Flow**: Integrated digital payment gateway with cryptographic transaction signature verification.
- **Review & Rating System**: 5-star rating and transparent client review feedback.

### 3. Superadmin Platform Management
- **User Account Management**: Admin CRUD controls for Clients, Owners, and Administrators.
- **Category Management**: Dynamic vehicle category management.
- **Platform Analytics & Financial Audit Logs**: Revenue tracking, fleet utilization, and transaction audits.

---

## 🏗️ System Architecture & Tech Stack

- **Backend**: Python 3.14 / Flask REST API
- **Frontend**: Responsive HTML5, Tailwind CSS, Three.js (3D WebGL), Leaflet.js (OpenStreetMap), FontAwesome
- **Database**: MySQL (with automatic zero-config fallback to SQLite for instant local testing)
- **AI Engine**: Hybrid heuristic + collaborative scoring engine (`services/ai_recommendation.py`)
- **Payment Gateway**: Cryptographic signature transaction simulation (`services/payment_gateway.py`)

---

## 🗄️ Database Schema (10 Tables)

The database schema matches the specifications outlined in the project report:

1. **`User`**: `(user_id, role, email, phone, name, password, created_at)`
2. **`Vehicle_Category`**: `(category_id, category_name, description)`
3. **`Vehicle`**: `(vehicle_id, owner_id, category_id, vehicle_name, location, price_per_day, availability, mileage, vehicle_3d_view, gps_device_id, image_url)`
4. **`Booking`**: `(booking_id, client_id, vehicle_id, start_date, end_date, booking_date, total_amount, status)`
5. **`Payment`**: `(payment_id, booking_id, amount, payment_method, transaction_id, payment_date, payment_status)`
6. **`Review`**: `(review_id, client_id, vehicle_id, booking_id, rating, review_text, review_date)`
7. **`GPS_Tracking`**: `(tracking_id, vehicle_id, latitude, longitude, tracked_at, speed)`
8. **`Maintenance`**: `(maintenance_id, vehicle_id, service_type, service_date, current_km, next_service_km, maintenance_status)`
9. **`Fine`**: `(fine_id, booking_id, fine_amount, reason, fine_date, payment_status)`
10. **`AI_Recommendation`**: `(recommendation_id, client_id, vehicle_id, recommendation_score, recommendation_reason, generated_at)`

---

## 🧮 Core Business Logic & Algorithms

### 1. Automated Fine Calculation
When a vehicle is returned after its scheduled `end_date`:
$$\text{Overdue Days} = \max(0, \text{Return Date} - \text{End Date})$$
$$\text{Fine Amount} = \text{BASE\_LATE\_FEE} + (\text{Overdue Days} \times \text{Daily Price} \times 1.5)$$

### 2. Kilometer-Based Maintenance Trigger
- **Status `OVERDUE`**: Triggered when $\text{current\_km} \ge \text{next\_service\_km}$.
- **Status `WARNING`**: Triggered when $(\text{next\_service\_km} - \text{current\_km}) \le 500\text{ km}$.
- **Status `OK`**: Healthy operating condition.

### 3. AI Recommendation Scoring Formula
- **Budget Affinity (35%)**: Measures price difference relative to client's past average spend.
- **Category Affinity (30%)**: Matches client's most frequently booked vehicle types.
- **Quality & Rating (25%)**: Incorporates historical 5-star customer review ratings.
- **Fleet Condition & Low Mileage (10%)**: Rewards lower odometer mileage and pristine vehicle maintenance.

---

## 🛠️ Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. (Optional) Setup MySQL Database
To use your local MySQL instance:
```bash
mysql -u root -p < schema.sql
```
Update `.env` or `config.py` with your MySQL credentials:
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=car4rent_db
```
*(Note: If MySQL is not running, the application automatically loads the SQLite engine with full seed data)*

### 3. Run Automated Tests
```bash
pytest
```

### 4. Start the Application Server
```bash
python app.py
```
Open your browser at **`http://127.0.0.1:5000`**

---

## 👥 Demo Logins Pre-Configured

- **Client**: `john.doe@gmail.com` (Pass: `client123`)
- **Owner**: `alex.fleet@car4rent.com` (Pass: `owner123`)
- **Admin**: `admin@car4rent.com` (Pass: `admin123`)
