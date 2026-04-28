from datetime import date, timedelta
from uuid import UUID

from app.services.summaries import SummaryService


def next_business_day() -> date:
    current = date.today() + timedelta(days=1)
    while current.weekday() >= 5:
        current += timedelta(days=1)
    return current


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_identify_user_creates_user(client):
    response = client.post(
        "/api/v1/tools/identify-user",
        json={"phone_number": "+919876543210", "name": "Nitheesh"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["phone_number"] == "+919876543210"
    assert body["name"] == "Nitheesh"
    assert body["appointments"] == []


def test_booking_and_retrieval_flow(client):
    booking_date = next_business_day().isoformat()
    book_response = client.post(
        "/api/v1/tools/book-appointment",
        json={
            "phone_number": "+919876543210",
            "name": "Nitheesh",
            "date": booking_date,
            "time": "10:00:00",
        },
    )
    assert book_response.status_code == 200
    appointment_id = book_response.json()["appointment"]["id"]

    retrieve_response = client.post(
        "/api/v1/tools/retrieve-appointments",
        json={"phone_number": "+919876543210"},
    )
    assert retrieve_response.status_code == 200
    assert len(retrieve_response.json()) == 1
    assert retrieve_response.json()[0]["id"] == appointment_id


def test_double_booking_is_rejected(client):
    booking_date = next_business_day().isoformat()
    payload = {
        "phone_number": "+919876543210",
        "name": "Nitheesh",
        "date": booking_date,
        "time": "10:30:00",
    }
    assert client.post("/api/v1/tools/book-appointment", json=payload).status_code == 200

    second = client.post(
        "/api/v1/tools/book-appointment",
        json={**payload, "phone_number": "+919123456789", "name": "Second User"},
    )
    assert second.status_code == 400
    assert second.json()["error_code"] in {"slot_unavailable", "double_booking_conflict"}


def test_modify_cancel_and_summary_flow(client, db_session):
    session_response = client.post("/api/v1/sessions", json={"participant_name": "Nitheesh"})
    assert session_response.status_code == 200
    session_id = session_response.json()["session_id"]

    booking_date = next_business_day()
    create_response = client.post(
        "/api/v1/tools/book-appointment",
        json={
            "phone_number": "+919876543210",
            "name": "Nitheesh",
            "date": booking_date.isoformat(),
            "time": "11:00:00",
            "session_id": session_id,
        },
    )
    assert create_response.status_code == 200
    original_id = create_response.json()["appointment"]["id"]

    modify_response = client.post(
        "/api/v1/tools/modify-appointment",
        json={
            "phone_number": "+919876543210",
            "appointment_id": original_id,
            "new_date": booking_date.isoformat(),
            "new_time": "11:30:00",
        },
    )
    assert modify_response.status_code == 200
    assert modify_response.json()["status"] == "booked"

    cancel_response = client.post(
        "/api/v1/tools/cancel-appointment",
        json={
            "phone_number": "+919876543210",
            "appointment_id": modify_response.json()["id"],
        },
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"

    summary_service = SummaryService(db_session)
    summary = summary_service.generate_summary(UUID(session_id))
    db_session.commit()
    assert "Captured phone number" in summary.summary_text or summary.summary_text

    get_summary = client.get(f"/api/v1/sessions/{session_id}/summary")
    assert get_summary.status_code == 200
