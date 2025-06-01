import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import MagicMock, patch
from uuid import uuid4
import mysql.connector
import json
from routers.apply import router, get_db_connection
from models import ApplicationForm, ApplicationType, GeneralApplicationRequest, ApplicationStatus, dnsApplicationForm

# Mock application data based on provided fake data
@pytest.fixture
def mock_application_data():
    return {
        "id": "1e7d439a-d61b-43a5-a97c-50a8df120001",
        "type": "DNS",
        "base_form": {
            "department": "Computer Science",
            "applicant_account": "s123456",
            "applicant_name": "Alice Chen",
            "applicant_phone": "0912345678",
            "applicant_email": "alice.chen@example.edu",
            "tech_contact_name": "Bob Wang",
            "tech_contact_phone": "0922333444",
            "tech_contact_email": "bob.wang@example.edu",
            "supervisor_name": "Dr. Lee",
            "supervisor_id": "A123456789",
            "supervisor_email": "dr.lee@example.edu",
            "apply_date": "2025-05-20",
            "status": "Pending"
        },
        "extra_form": {
            "applicant_unit": "CS Department",
            "domain_name": "cs.example.edu",
            "application_project": "Student Portal",
            "dns_manage_account": "dns_admin",
            "reason": "Hosting department web portal"
        }
    }

@pytest.fixture
def sample_base_form():
    return ApplicationForm(
        department="Computer Science",
        applicant_account="s123456",
        applicant_name="Alice Chen",
        applicant_phone="0912345678",
        applicant_email="alice.chen@example.edu",
        tech_contact_name="Bob Wang",
        tech_contact_phone="0922333444",
        tech_contact_email="bob.wang@example.edu",
        supervisor_name="Dr. Lee",
        supervisor_id="A123456789",
        supervisor_email="dr.lee@example.edu",
        apply_date="2025-05-20",
        status=ApplicationStatus.pending
    )

@pytest.fixture
def sample_dns_form():
    return dnsApplicationForm(
        applicant_unit="CS Department",
        domain_name="cs.example.edu",
        application_project="Student Portal",
        dns_manage_account="dns_admin",
        reason="Hosting department web portal"
    )

@pytest.fixture
def sample_request(sample_base_form, sample_dns_form):
    return GeneralApplicationRequest(
        application_type=ApplicationType.dns,
        baseForm=sample_base_form,
        additionForm=sample_dns_form.dict()
    )

# Mock database connection
@pytest.fixture
def mock_db_connection():
    with patch('routers.apply.get_db_connection') as mock_conn:
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_connection
        yield mock_connection, mock_cursor

# Create a test client
@pytest_asyncio.fixture
async def client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)

@pytest.mark.asyncio
async def test_create_application_success(client, mock_db_connection, sample_request):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 1
    app_id = "1e7d439a-d61b-43a5-a97c-50a8df120001"

    with patch('uuid.uuid4', return_value=app_id):
        response = client.post("/create", json=sample_request.dict())
    
    assert response.status_code == 200
    assert response.json() == {
        "application_id": app_id,
        "message": f"Thanks for your {sample_request.application_type.value} apply!"
    }
    mock_cursor.execute.assert_called()
    mock_connection.commit.assert_called()
    mock_cursor.close.assert_called()
    mock_connection.close.assert_called()

@pytest.mark.asyncio
async def test_create_application_invalid_dns_form(client, sample_base_form):
    invalid_request = GeneralApplicationRequest(
        application_type=ApplicationType.dns,
        baseForm=sample_base_form,
        additionForm={"invalid": "data"}
    )
    response = client.post("/create", json=invalid_request.dict())
    assert response.status_code == 400
    assert "Invalid DNS form" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_application_unsupported_type(client, sample_base_form):
    invalid_request = GeneralApplicationRequest(
        application_type="invalid_type",
        baseForm=sample_base_form,
        additionForm={}
    )
    response = client.post("/create", json=invalid_request.dict())
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported application type"

@pytest.mark.asyncio
async def test_create_application_db_error(client, mock_db_connection, sample_request):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = mysql.connector.Error("DB Error")
    
    response = client.post("/create", json=sample_request.dict())
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_all_applications_success(client, mock_db_connection, mock_application_data):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchall.return_value = [
        {
            "id": mock_application_data["id"],
            "type": mock_application_data["type"],
            "base_form": json.dumps(mock_application_data["base_form"]),
            "extra_form": json.dumps(mock_application_data["extra_form"])
        }
    ]
    
    response = client.get("/getAll")
    assert response.status_code == 200
    assert response.json() == {
        mock_application_data["id"]: {
            "type": mock_application_data["type"],
            "base": mock_application_data["base_form"],
            "extra": mock_application_data["extra_form"]
        }
    }
    mock_cursor.execute.assert_called()
    mock_cursor.close.assert_called()
    mock_connection.close.assert_called()

@pytest.mark.asyncio
async def test_get_all_applications_db_error(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = mysql.connector.Error("DB Error")
    
    response = client.get("/getAll")
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_applications_by_user_success(client, mock_db_connection, mock_application_data):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchall.return_value = [
        {
            "id": mock_application_data["id"],
            "type": mock_application_data["type"],
            "base_form": json.dumps(mock_application_data["base_form"]),
            "extra_form": json.dumps(mock_application_data["extra_form"])
        }
    ]
    
    response = client.get("/my-applications", headers={"X-User-Id": "s123456"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0] == {
        "application_id": mock_application_data["id"],
        "type": mock_application_data["type"],
        "base": mock_application_data["base_form"],
        "extra": mock_application_data["extra_form"]
    }
    mock_cursor.execute.assert_called()
    mock_cursor.close.assert_called()
    mock_connection.close.assert_called()

@pytest.mark.asyncio
async def test_get_applications_by_user_no_header(client):
    response = client.get("/my-applications")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing X-User-Id header"

@pytest.mark.asyncio
async def test_get_applications_by_user_no_results(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchall.return_value = []
    
    response = client.get("/my-applications", headers={"X-User-Id": "s123456"})
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_application_success(client, mock_db_connection, mock_application_data):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = {
        "id": mock_application_data["id"],
        "type": mock_application_data["type"],
        "base_form": json.dumps(mock_application_data["base_form"]),
        "extra_form": json.dumps(mock_application_data["extra_form"])
    }
    
    response = client.get(f"/{mock_application_data['id']}")
    assert response.status_code == 200
    assert response.json() == {
        "type": mock_application_data["type"],
        "base": mock_application_data["base_form"],
        "extra": mock_application_data["extra_form"]
    }

@pytest.mark.asyncio
async def test_get_application_not_found(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None
    
    response = client.get("/1e7d439a-d61b-43a5-a97c-50a8df120001")
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"

@pytest.mark.asyncio
async def test_get_application_db_error(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = mysql.connector.Error("DB Error")
    
    response = client.get("/1e7d439a-d61b-43a5-a97c-50a8df120001")
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_application_success(client, mock_db_connection, sample_request):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 1
    
    response = client.put("/1e7d439a-d61b-43a5-a97c-50a8df120001", json=sample_request.dict())
    assert response.status_code == 200
    assert response.json() == {
        "application_id": "1e7d439a-d61b-43a5-a97c-50a8df120001",
        "message": "Application updated successfully"
    }
    mock_cursor.execute.assert_called()
    mock_connection.commit.assert_called()

@pytest.mark.asyncio
async def test_update_application_not_found(client, mock_db_connection, sample_request):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 0
    
    response = client.put("/1e7d439a-d61b-43a5-a97c-50a8df120001", json=sample_request.dict())
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"

@pytest.mark.asyncio
async def test_update_application_invalid_dns_form(client, mock_db_connection, sample_base_form):
    invalid_request = GeneralApplicationRequest(
        application_type=ApplicationType.dns,
        baseForm=sample_base_form,
        additionForm={"invalid": "data"}
    )
    response = client.put("/1e7d439a-d61b-43a5-a97c-50a8df120001", json=invalid_request.dict())
    assert response.status_code == 400
    assert "Invalid DNS form" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_application_unsupported_type(client, mock_db_connection, sample_base_form):
    invalid_request = GeneralApplicationRequest(
        application_type="invalid_type",
        baseForm=sample_base_form,
        additionForm={}
    )
    response = client.put("/1e7d439a-d61b-43a5-a97c-50a8df120001", json=invalid_request.dict())
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported application type"

@pytest.mark.asyncio
async def test_update_application_db_error(client, mock_db_connection, sample_request):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = mysql.connector.Error("DB Error")
    
    response = client.put("/1e7d439a-d61b-43a5-a97c-50a8df120001", json=sample_request.dict())
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_cancel_application_success(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 1
    
    response = client.put("/cancel/1e7d439a-d61b-43a5-a97c-50a8df120001")
    assert response.status_code == 200
    assert response.json() == {
        "application_id": "1e7d439a-d61b-43a5-a97c-50a8df120001",
        "message": "Application canceled successfully"
    }

@pytest.mark.asyncio
async def test_cancel_application_not_found(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 0
    
    response = client.put("/cancel/1e7d439a-d61b-43a5-a97c-50a8df120001")
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"

@pytest.mark.asyncio
async def test_cancel_application_db_error(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = mysql.connector.Error("DB Error")
    
    response = client.put("/cancel/1e7d439a-d61b-43a5-a97c-50a8df120001")
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_approve_application_success(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 1
    
    response = client.put("/approved/1e7d439a-d61b-43a5-a97c-50a8df120001")
    assert response.status_code == 200
    assert response.json() == {
        "application_id": "1e7d439a-d61b-43a5-a97c-50a8df120001",
        "message": "Application approved successfully"
    }

@pytest.mark.asyncio
async def test_approve_application_not_found(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 0
    
    response = client.put("/approved/1e7d439a-d61b-43a5-a97c-50a8df120001")
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"

@pytest.mark.asyncio
async def test_approve_application_db_error(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = mysql.connector.Error("DB Error")
    
    response = client.put("/approved/1e7d439a-d61b-43a5-a97c-50a8df120001")
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_reject_application_success(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 1
    
    response = client.put("/rejected/1e7d439a-d61b-43a5-a97c-50a8df120001")
    assert response.status_code == 200
    assert response.json() == {
        "application_id": "1e7d439a-d61b-43a5-a97c-50a8df120001",
        "message": "Application rejected successfully"
    }

@pytest.mark.asyncio
async def test_reject_application_not_found(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 0
    
    response = client.put("/rejected/1e7d439a-d61b-43a5-a97c-50a8df120001")
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"

@pytest.mark.asyncio
async def test_reject_application_db_error(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = mysql.connector.Error("DB Error")
    
    response = client.put("/rejected/1e7d439a-d61b-43a5-a97c-50a8df120001")
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_application_success(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 1
    
    response = client.delete("/1e7d439a-d61b-43a5-a97c-50a8df120001")
    assert response.status_code == 200
    assert response.json() == {
        "application_id": "1e7d439a-d61b-43a5-a97c-50a8df120001",
        "message": "Application deleted successfully"
    }

@pytest.mark.asyncio
async def test_delete_application_not_found(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 0
    
    response = client.delete("/1e7d439a-d61b-43a5-a97c-50a8df120001")
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"

@pytest.mark.asyncio
async def test_delete_application_db_error(client, mock_db_connection):
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = mysql.connector.Error("DB Error")
    
    response = client.delete("/1e7d439a-d61b-43a5-a97c-50a8df120001")
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_db_connection_failure():
    with patch('mysql.connector.connect', side_effect=mysql.connector.Error("Connection failed")):
        with pytest.raises(HTTPException) as exc:
            get_db_connection()
        assert exc.value.status_code == 500
        assert "Database connection failed" in exc.value.detail