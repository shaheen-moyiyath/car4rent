import pytest
from app import create_app
from database import Database

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'healthy'

def test_vehicle_catalog_and_filter(client):
    res = client.get('/api/vehicles')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert len(data['vehicles']) >= 5

def test_booking_and_payment_flow(client):
    # 1. Create Booking
    book_payload = {
        "client_id": 4,
        "vehicle_id": 1,
        "start_date": "2026-11-01",
        "end_date": "2026-11-04"
    }
    b_res = client.post('/api/bookings', json=book_payload)
    assert b_res.status_code == 201
    b_data = b_res.get_json()
    booking_id = b_data['booking_id']
    total_amount = b_data['total_amount']

    # 2. Checkout Payment
    pay_payload = {
        "booking_id": booking_id,
        "amount": total_amount,
        "payment_method": "Credit Card"
    }
    p_res = client.post('/api/payments/checkout', json=pay_payload)
    assert p_res.status_code == 200
    p_data = p_res.get_json()
    assert p_data['success'] is True
    assert p_data['payment_status'] == 'Completed'
    assert p_data['transaction_id'].startswith('TXN-C4R-')

def test_gps_telemetry(client):
    res = client.get('/api/gps/vehicle/1/live')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert 'latitude' in data
    assert 'longitude' in data
