import sys
import os
# This will add apply_service to the module path, allowing main.py to import correctly
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import app
from fastapi.testclient import TestClient
import pytest

client = TestClient(app)

mock_data = {
    "baseForm": {
        "department": "資訊工程系",
        "applicant_account": "b112345678",
        "applicant_name": "小明",
        "applicant_phone": "0912345678",
        "applicant_email": "b112345678@gs.ncku.edu.tw",
        "tech_contact_name": "技術人員小華",
        "tech_contact_phone": "0922333444",
        "tech_contact_email": "tech@example.com",
        "supervisor_name": "指導教授小林",
        "supervisor_id": "F123456789",
        "supervisor_email": "supervisor@ncku.edu.tw"
    },
    "additionForm": {
        "applicant_unit": "資訊工程系 網路組",
        "domain_name": "example.csie.ncku.edu.tw",
        "application_project": "課程網站平台",
        "dns_manage_account": "dns_admin",
        "reason": "提供學生課程資料與報名系統"
    }
}


def test_create_application():
    response = client.post("/apply/", json=mock_data)
    assert response.status_code == 200
    assert "application_id" in response.json()

def test_get_all_applications():
    response = client.get("/apply/")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

# Test read
def test_get_application_by_id():
    # Creat
    post_res = client.post("/apply/", json=mock_data)
    app_id = post_res.json()["application_id"]

    # Read by ID
    get_res = client.get(f"/apply/{app_id}")
    assert get_res.status_code == 200
    assert get_res.json()["applicant_account"] == "b112345678"

    # Not exist ID
    non_existent_id = "not-in-db-id"
    response = client.get(f"/apply/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"

# Test update
def test_update_application():
    # Create
    post_res = client.post("/apply/", json=mock_data)
    app_id = post_res.json()["application_id"]

    # Update
    updated_form = mock_data["baseForm"].copy()
    updated_form["applicant_name"] = "小王"
    update_res = client.put(f"/apply/{app_id}", json=updated_form)

    assert update_res.status_code == 200
    assert update_res.json()["message"] == "Application updated successfully"

    # Not exist ID
    non_existent_id = "not-in-db-id"
    response = client.put(f"/apply/{non_existent_id}", json=updated_form)
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"

def test_delete_application():
    # Create
    post_res = client.post("/apply/", json=mock_data)
    app_id = post_res.json()["application_id"]

    # Delete
    del_res = client.delete(f"/apply/{app_id}")
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Application deleted successfully"

    # Not exist ID
    non_existent_id = "not-in-db-id"
    del_res = client.delete(f"/apply/{non_existent_id}")
    assert del_res.status_code == 404
    assert del_res.json()["detail"] == "Application not found"
    

