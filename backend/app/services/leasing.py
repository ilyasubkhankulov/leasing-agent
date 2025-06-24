import requests
from typing import Dict, Any
from datetime import datetime, timedelta


def propose_tour(lead_preferences: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(
        "https://api.leasing-system.com/v1/tours/propose",
        json={
            "lead_id": lead_preferences.get("lead_id"),
            "preferred_time": lead_preferences.get("preferred_time"),
            "unit_type": lead_preferences.get("unit_type")
        }
    )
    data = response.json()
    return {
        "action": "propose_tour",
        "tour_time": data.get("suggested_time", "11:00 AM"),
        "tour_date": data.get("suggested_date", (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")),
        "unit_id": data.get("unit_id", "A205"),
        "confirmation_required": True
    }


def ask_clarification(unclear_request: str) -> Dict[str, Any]:
    response = requests.post(
        "https://api.leasing-system.com/v1/clarification/generate",
        json={"user_message": unclear_request}
    )
    data = response.json()
    return {
        "action": "ask_clarification", 
        "clarifying_question": data.get("question", "Which date works best for you?"),
        "suggested_options": data.get("options", ["This week", "Next week", "Specific date"]),
        "context": unclear_request
    }


def handoff_human(issue_details: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(
        "https://api.leasing-system.com/v1/handoff/create",
        json={
            "reason": issue_details.get("reason"),
            "lead_id": issue_details.get("lead_id"),
            "conversation_history": issue_details.get("conversation_history"),
            "priority": issue_details.get("priority", "normal")
        }
    )
    data = response.json()
    return {
        "action": "handoff_human",
        "agent_id": data.get("assigned_agent_id", "agent_001"),
        "estimated_wait_time": data.get("wait_time_minutes", 5),
        "ticket_id": data.get("ticket_id", "TICKET_12345"),
        "handoff_message": "Connecting you with a human agent who can better assist you."
    }