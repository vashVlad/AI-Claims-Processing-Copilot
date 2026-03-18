def calculate_priority(analysis: dict) -> dict:
    score = 0

    # Urgency (0–40 points)
    urgency_scores = {"low": 10, "medium": 25, "high": 40}
    score += urgency_scores.get(analysis.get("urgency_level", "low"), 0)

    # Injury (0–30 points)
    if analysis.get("injury_present", "no").lower() == "yes":
        score += 30

    # Fraud risk (0–20 points)
    fraud_scores = {"low": 0, "medium": 10, "high": 20}
    score += fraud_scores.get(analysis.get("fraud_risk", "low"), 0)

    # Damage length as a rough severity proxy (0–10 points)
    damage = analysis.get("damage_description", "")
    if len(damage) > 50:
        score += 10
    elif len(damage) > 20:
        score += 5

    # Recommendation
    if score >= 80:
        recommendation = "Immediate Review"
    elif score >= 50:
        recommendation = "Standard Processing"
    else:
        recommendation = "Low Priority"

    return {
        "priority_score": score,
        "recommendation": recommendation
    }