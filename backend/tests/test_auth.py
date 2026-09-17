def test_register_and_login(client):
    reg_data = {
        "name": "Jane Scholar",
        "email": "jane@studygen.ai",
        "password": "securepassword123"
    }
    response = client.post("/api/auth/register", json=reg_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "jane@studygen.ai"

    # Test login with newly registered credentials
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "jane@studygen.ai", "password": "securepassword123"}
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    # Test duplicate registration rejection
    dup_resp = client.post("/api/auth/register", json=reg_data)
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"]


def test_guest_login(client):
    response = client.post("/api/auth/guest")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "guest@studygen.ai"
    assert data["user"]["name"] == "Demo Student"

    # Second call should return the existing guest user without creating duplicate error
    second_resp = client.post("/api/auth/guest")
    assert second_resp.status_code == 200
    assert second_resp.json()["user"]["email"] == "guest@studygen.ai"

