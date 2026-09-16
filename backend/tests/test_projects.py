def test_project_crud(client, auth_headers):
    # Create project
    proj_payload = {
        "name": "Wireless Sensor Networks",
        "subject": "IoT",
        "description": "Architectures, routing protocols, and power management."
    }
    create_resp = client.post("/api/projects", json=proj_payload, headers=auth_headers)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["name"] == "Wireless Sensor Networks"
    assert created["subject"] == "IoT"
    project_id = created["id"]

    # List projects
    list_resp = client.get("/api/projects", headers=auth_headers)
    assert list_resp.status_code == 200
    projects = list_resp.json()
    assert any(p["id"] == project_id for p in projects)

    # Get single project
    get_resp = client.get(f"/api/projects/{project_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == project_id

    # Update project
    update_payload = {"name": "Advanced Wireless Sensor Networks"}
    put_resp = client.put(f"/api/projects/{project_id}", json=update_payload, headers=auth_headers)
    assert put_resp.status_code == 200
    assert put_resp.json()["name"] == "Advanced Wireless Sensor Networks"

    # Delete project
    del_resp = client.delete(f"/api/projects/{project_id}", headers=auth_headers)
    assert del_resp.status_code == 200

    # Verify deleted
    get_del = client.get(f"/api/projects/{project_id}", headers=auth_headers)
    assert get_del.status_code == 404
