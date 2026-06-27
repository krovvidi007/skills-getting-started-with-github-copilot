import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    """Reset in-memory activities after each test to prevent state leakage."""
    # Arrange: capture original activities state
    original_activities = copy.deepcopy(activities)
    
    # Act: allow test to run
    yield
    
    # Assert/Cleanup: restore original state
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_index():
    """Test that the root path redirects to the static index page."""
    # Arrange
    expected_status_code = 307
    expected_location = "/static/index.html"
    
    # Act
    response = client.get("/", follow_redirects=False)
    
    # Assert
    assert response.status_code == expected_status_code
    assert response.headers["location"] == expected_location


def test_get_activities_returns_seeded_activities():
    """Test that GET /activities returns the seeded activity data."""
    # Arrange
    expected_status_code = 200
    
    # Act
    response = client.get("/activities")
    data = response.json()
    
    # Assert
    assert response.status_code == expected_status_code
    assert isinstance(data, dict)
    assert len(data) > 0
    
    # Verify expected activity structure
    for activity_name, activity_data in data.items():
        assert "description" in activity_data
        assert "schedule" in activity_data
        assert "max_participants" in activity_data
        assert "participants" in activity_data
        assert isinstance(activity_data["participants"], list)


def test_signup_for_activity_adds_participant():
    """Test that a participant can successfully sign up for an activity."""
    # Arrange
    activity_name = next(iter(activities))
    new_email = "new_student@mergington.edu"
    expected_status_code = 200
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email},
    )
    
    # Assert
    assert response.status_code == expected_status_code
    assert new_email in activities[activity_name]["participants"]


def test_signup_for_missing_activity_returns_404():
    """Test that signing up for a non-existent activity returns 404."""
    # Arrange
    missing_activity = "Non Existent Activity"
    email = "student@mergington.edu"
    expected_status_code = 404
    
    # Act
    response = client.post(
        f"/activities/{missing_activity}/signup",
        params={"email": email},
    )
    
    # Assert
    assert response.status_code == expected_status_code
    assert "Activity not found" in response.json()["detail"]


def test_signup_duplicate_email_returns_400():
    """Test that signing up with a duplicate email returns 400."""
    # Arrange
    activity_name = next(iter(activities))
    existing_email = activities[activity_name]["participants"][0]
    expected_status_code = 400
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email},
    )
    
    # Assert
    assert response.status_code == expected_status_code
    assert "already signed up" in response.json()["detail"]


def test_unregister_removes_existing_participant():
    """Test that a participant can successfully unregister from an activity."""
    # Arrange
    activity_name = next(iter(activities))
    email_to_remove = activities[activity_name]["participants"][0]
    expected_status_code = 200
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email_to_remove},
    )
    
    # Assert
    assert response.status_code == expected_status_code
    assert email_to_remove not in activities[activity_name]["participants"]


def test_unregister_missing_activity_returns_404():
    """Test that unregistering from a non-existent activity returns 404."""
    # Arrange
    missing_activity = "Non Existent Activity"
    email = "student@mergington.edu"
    expected_status_code = 404
    
    # Act
    response = client.delete(
        f"/activities/{missing_activity}/unregister",
        params={"email": email},
    )
    
    # Assert
    assert response.status_code == expected_status_code
    assert "Activity not found" in response.json()["detail"]


def test_unregister_nonparticipant_returns_404():
    """Test that unregistering a non-participant returns 404."""
    # Arrange
    activity_name = next(iter(activities))
    non_participant_email = "not_registered@mergington.edu"
    expected_status_code = 404
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": non_participant_email},
    )
    
    # Assert
    assert response.status_code == expected_status_code
    assert "not signed up" in response.json()["detail"]
