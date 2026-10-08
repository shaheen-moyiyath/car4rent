from flask import Blueprint, request, jsonify
from database import Database
from services.ai_recommendation import AIRecommendationEngine

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

@ai_bp.route('/recommendations/<int:client_id>', methods=['GET'])
def get_recommendations(client_id):
    """
    Computes and returns personalized AI recommendations for a client
    based on budget history, category affinity, and vehicle ratings.
    """
    top_n = request.args.get('top_n', 5)
    recs = AIRecommendationEngine.generate_recommendations_for_client(client_id, int(top_n))
    return jsonify({
        "success": True,
        "client_id": client_id,
        "recommendations": recs,
        "total": len(recs)
    })
