from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from urllib.parse import quote

from src.app import app, activities


@pytest.fixture
def preserve_activities():
    """Deep-copy `activities` and restore after each test to avoid cross-test state."""
    original = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


@pytest.fixture
def client():
    """Return a TestClient for the FastAPI app."""
    return TestClient(app)


def test_get_activities(client, preserve_activities):
    # Arrange: (preserve_activities fixture ensures original state)
    # Act
    resp = client.get("/activities")
    # Assert
    assert resp.status_code == 200
    assert resp.json() == activities


def test_signup_success(client, preserve_activities):
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    # Arrange: ensure email not already signed up
    assert email not in activities[activity_name]["participants"]

    # Act
    path = f"/activities/{quote(activity_name)}/signup"
    resp = client.post(path, params={"email": email})

    # Assert
    assert resp.status_code == 200
    body = resp.json()
    assert "Signed up" in body.get("message", "")
    assert email in activities[activity_name]["participants"]


def test_signup_duplicate(client, preserve_activities):
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"
    # Arrange: ensure the email is present once
    assert existing_email in activities[activity_name]["participants"]
    before_count = activities[activity_name]["participants"].count(existing_email)

    # Act
    path = f"/activities/{quote(activity_name)}/signup"
    resp = client.post(path, params={"email": existing_email})

    # Assert
    assert resp.status_code == 400
    assert resp.json().get("detail") == "Student is already signed up"
    after_count = activities[activity_name]["participants"].count(existing_email)
    assert after_count == before_count


def test_remove_participant_success(client, preserve_activities):
    activity_name = "Basketball Team"
    email = "alex@mergington.edu"
    # Arrange: ensure email is present
    assert email in activities[activity_name]["participants"]

    # Act
    path = f"/activities/{quote(activity_name)}/participants"
    resp = client.delete(path, params={"email": email})

    # Assert
    assert resp.status_code == 200
    body = resp.json()
    assert "Removed" in body.get("message", "")
    assert email not in activities[activity_name]["participants"]


def test_remove_nonexistent_participant(client, preserve_activities):
    activity_name = "Tennis Club"
    email = "notfound@mergington.edu"
    # Arrange: ensure email is not present
    assert email not in activities[activity_name]["participants"]

    # Act
    path = f"/activities/{quote(activity_name)}/participants"
    resp = client.delete(path, params={"email": email})

    # Assert
    assert resp.status_code == 404
    assert resp.json().get("detail") == "Participant not found"
