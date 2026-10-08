import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from config import Config
from database import Database

# Import Route Blueprints
from routes.auth_routes import auth_bp
from routes.vehicle_routes import vehicle_bp
from routes.booking_routes import booking_bp
from routes.payment_routes import payment_bp
from routes.gps_routes import gps_bp
from routes.maintenance_routes import maintenance_bp
from routes.review_routes import review_bp
from routes.fine_routes import fine_bp
from routes.ai_routes import ai_bp
from routes.admin_routes import admin_bp

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(Config)
    CORS(app, supports_credentials=True)

    # Initialize Database Schema & Seed Data (Auto fallback check)
    Database.init_sqlite_db()

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(vehicle_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(gps_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(fine_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(admin_bp)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/health')
    def health_check():
        _, engine = Database.get_connection()
        return jsonify({
            "status": "healthy",
            "platform": "Car4Rent: A Web Based Car Rental System",
            "database_engine": engine,
            "version": "2.0.0"
        })

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    print(f"==================================================")
    print(f" Car4Rent Multi-Owner Platform Server Running")
    print(f" Local Web UI: http://127.0.0.1:{port}")
    print(f"==================================================")
    app.run(host='0.0.0.0', port=port, debug=True)
