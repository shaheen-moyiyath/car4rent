import pytest
from database import Database
from services.maintenance_service import MaintenanceService

@pytest.fixture(autouse=True)
def setup_test_db():
    Database.init_sqlite_db()

def test_maintenance_status_evaluation():
    # Vehicle #1 has mileage 24800, next service at 30000 -> Status OK
    res = MaintenanceService.check_vehicle_maintenance_status(1)
    assert res['success'] is True
    assert res['alert_status'] == 'OK'
    assert res['is_alert_triggered'] is False

def test_maintenance_status_warning_and_overdue():
    # Set vehicle mileage to 29700 (within 500km of 30000) -> WARNING
    res = MaintenanceService.update_odometer_and_evaluate(1, 29700)
    assert res['alert_status'] == 'WARNING'
    assert res['is_alert_triggered'] is True

    # Set vehicle mileage to 30050 (exceeded 30000) -> OVERDUE
    res = MaintenanceService.update_odometer_and_evaluate(1, 30050)
    assert res['alert_status'] == 'OVERDUE'
    assert res['is_alert_triggered'] is True

    # Reset odometer back to healthy state for other tests
    MaintenanceService.log_maintenance_service(1, "Post-Test Reset Inspection", 30050, 10000)
