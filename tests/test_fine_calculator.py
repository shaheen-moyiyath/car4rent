import pytest
from database import Database
from services.fine_calculator import FineCalculatorService
from config import Config

@pytest.fixture(autouse=True)
def setup_test_db():
    Database.init_sqlite_db()

def test_fine_calculation_on_time():
    # Booking #1 ended on 2026-09-24. Returning on 2026-09-24 should yield 0 fine
    res = FineCalculatorService.calculate_overdue_fine(1, "2026-09-24")
    assert res['success'] is True
    assert res['is_overdue'] is False
    assert res['fine_amount'] == 0.0

def test_fine_calculation_overdue():
    # Booking #1 ended on 2026-09-24. Returning on 2026-09-27 is 3 days late
    # Daily price for vehicle #1 is 95.00
    # Expected fine: BASE_LATE_FEE (25.0) + (3 * 95.0 * 1.5) = 25.0 + 427.5 = 452.50
    res = FineCalculatorService.calculate_overdue_fine(1, "2026-09-27")
    assert res['success'] is True
    assert res['is_overdue'] is True
    assert res['overdue_days'] == 3
    assert res['fine_amount'] == 452.50
    assert "Late return: 3 day(s) overdue" in res['reason']
