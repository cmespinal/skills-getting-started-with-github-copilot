from copy import deepcopy

import httpx
import pytest

from src.app import activities, app


@pytest.fixture(autouse=True)
def restore_activity_state():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as test_client:
        yield test_client


@pytest.mark.anyio
async def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = await client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


@pytest.mark.anyio
async def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activity = activities["Chess Club"]

    # Act
    response = await client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"] == expected_activity


@pytest.mark.anyio
async def test_signup_registers_student(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"

    # Act
    response = await client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


@pytest.mark.anyio
async def test_signup_rejects_duplicate_student(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = await client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


@pytest.mark.anyio
async def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Robotics Club"
    email = "new.student@mergington.edu"

    # Act
    response = await client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


@pytest.mark.anyio
async def test_unregister_removes_student(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = await client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in activities[activity_name]["participants"]


@pytest.mark.anyio
async def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Robotics Club"
    email = "student@mergington.edu"

    # Act
    response = await client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


@pytest.mark.anyio
async def test_unregister_rejects_student_not_signed_up(client):
    # Arrange
    activity_name = "Chess Club"
    email = "not.registered@mergington.edu"

    # Act
    response = await client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
