import pytest
from database import Database
from services.ai_recommendation import AIRecommendationEngine

@pytest.fixture(autouse=True)
def setup_test_db():
    Database.init_sqlite_db()

def test_ai_recommendation_generation():
    # Client #4 (John Doe) has previous bookings for EV and SUV
    recs = AIRecommendationEngine.generate_recommendations_for_client(4, top_n=3)
    assert len(recs) > 0
    # Recommendation score should be calculated between 40 and 100
    assert 40 <= recs[0]['recommendation_score'] <= 100
    # Must have non-empty explainable AI reason
    assert len(recs[0]['recommendation_reason']) > 0
