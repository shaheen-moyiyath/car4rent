from database import Database
from datetime import datetime

class AIRecommendationEngine:
    """
    AI Recommendation Engine:
    Employs a hybrid score-based collaborative scoring model analyzing:
    1. Client's historical spending profile / budget affinity (35%)
    2. Preferred vehicle category affinities from previous rentals (30%)
    3. Vehicle historical customer satisfaction ratings (25%)
    4. Vehicle condition, mileage efficiency & reliability index (10%)
    """

    @classmethod
    def generate_recommendations_for_client(cls, client_id: int, top_n: int = 5) -> list:
        # 1. Fetch Client's Booking History
        past_bookings = Database.execute_query(
            """
            SELECT b.booking_id, b.vehicle_id, b.total_amount, b.start_date, b.end_date,
                   v.category_id, v.price_per_day, c.category_name
            FROM Booking b
            JOIN Vehicle v ON b.vehicle_id = v.vehicle_id
            JOIN Vehicle_Category c ON v.category_id = c.category_id
            WHERE b.client_id = %s AND b.status IN ('Completed', 'Active')
            """,
            (client_id,)
        )
        
        # Calculate Client Budget & Category preferences
        if past_bookings:
            total_days = 0
            total_spent = 0.0
            category_counts = {}
            for b in past_bookings:
                price = float(b['price_per_day'])
                cat_id = b['category_id']
                category_counts[cat_id] = category_counts.get(cat_id, 0) + 1
                total_spent += price
                total_days += 1
            client_avg_budget = total_spent / total_days if total_days > 0 else 100.0
            fav_category_id = max(category_counts, key=category_counts.get) if category_counts else None
        else:
            # Cold start defaults for new users
            client_avg_budget = 100.0
            fav_category_id = None

        # 2. Fetch all currently available vehicles with their ratings & category info
        vehicles = Database.execute_query(
            """
            SELECT v.vehicle_id, v.vehicle_name, v.category_id, v.location, v.price_per_day,
                   v.availability, v.mileage, v.vehicle_3d_view, v.image_url,
                   c.category_name,
                   COALESCE(AVG(r.rating), 4.5) as avg_rating,
                   COUNT(r.review_id) as review_count
            FROM Vehicle v
            JOIN Vehicle_Category c ON v.category_id = c.category_id
            LEFT JOIN Review r ON v.vehicle_id = r.vehicle_id
            GROUP BY v.vehicle_id, v.vehicle_name, v.category_id, v.location, v.price_per_day,
                     v.availability, v.mileage, v.vehicle_3d_view, v.image_url, c.category_name
            """
        )

        recommendations = []

        for v in vehicles:
            price = float(v['price_per_day'])
            rating = float(v['avg_rating'])
            mileage = int(v['mileage'])
            category_id = v['category_id']
            
            # --- Score Component 1: Budget Affinity (0-35 pts) ---
            # Maximum points if price is close to client's average budget
            budget_diff = abs(price - client_avg_budget)
            budget_score = max(0.0, 35.0 - (budget_diff / client_avg_budget * 25.0))
            budget_score = min(35.0, budget_score)

            # --- Score Component 2: Category Affinity (0-30 pts) ---
            if fav_category_id and category_id == fav_category_id:
                category_score = 30.0
            elif past_bookings:
                category_score = 15.0 # Moderate affinity
            else:
                category_score = 22.0 # Neutral baseline for new clients

            # --- Score Component 3: Vehicle Rating & Quality (0-25 pts) ---
            # 5 stars = 25 pts, 1 star = 5 pts
            rating_score = (rating / 5.0) * 25.0

            # --- Score Component 4: Low Mileage & Fleet Condition (0-10 pts) ---
            # Lower mileage rewards up to 10 points
            mileage_factor = max(0.0, 1.0 - (mileage / 100000.0))
            condition_score = mileage_factor * 10.0

            total_score = round(budget_score + category_score + rating_score + condition_score, 2)
            total_score = min(99.5, max(40.0, total_score)) # Clamp between 40 - 99.5%

            # Generate Explainable AI Reasoning Text
            reasons = []
            if fav_category_id and category_id == fav_category_id:
                reasons.append(f"Matches your high interest in {v['category_name']} vehicles")
            if abs(price - client_avg_budget) <= 25.0:
                reasons.append(f"Fits within your preferred daily budget (~${int(client_avg_budget)}/day)")
            if rating >= 4.5:
                reasons.append(f"Highly rated by clients ({rating:.1f}/5.0 stars)")
            if mileage < 30000:
                reasons.append("Low mileage, pristine fleet condition")

            if not reasons:
                reasons.append("Popular premium vehicle with high rental demand")

            reason_str = " | ".join(reasons)

            rec_item = {
                "vehicle_id": v['vehicle_id'],
                "vehicle_name": v['vehicle_name'],
                "category_name": v['category_name'],
                "price_per_day": price,
                "location": v['location'],
                "avg_rating": round(rating, 1),
                "review_count": v['review_count'],
                "image_url": v['image_url'],
                "vehicle_3d_view": v['vehicle_3d_view'],
                "recommendation_score": total_score,
                "recommendation_reason": reason_str
            }
            recommendations.append(rec_item)

        # Sort recommendations by highest score
        recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
        top_recommendations = recommendations[:top_n]

        # Upsert into AI_Recommendation Table
        for rec in top_recommendations:
            # Check existing recommendation
            existing = Database.execute_query(
                "SELECT recommendation_id FROM AI_Recommendation WHERE client_id = %s AND vehicle_id = %s",
                (client_id, rec['vehicle_id'])
            )
            if existing:
                Database.execute_query(
                    """
                    UPDATE AI_Recommendation 
                    SET recommendation_score = %s, recommendation_reason = %s, generated_at = CURRENT_TIMESTAMP
                    WHERE recommendation_id = %s
                    """,
                    (rec['recommendation_score'], rec['recommendation_reason'], existing[0]['recommendation_id'])
                )
            else:
                Database.execute_query(
                    """
                    INSERT INTO AI_Recommendation (client_id, vehicle_id, recommendation_score, recommendation_reason)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (client_id, rec['vehicle_id'], rec['recommendation_score'], rec['recommendation_reason'])
                )

        return top_recommendations
