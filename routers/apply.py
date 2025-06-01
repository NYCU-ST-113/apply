from fastapi import APIRouter, HTTPException, Request
from models import ApplicationForm, ApplicationType, GeneralApplicationRequest, ApplicationResponse, dnsApplicationForm, ApplicationStatus
from uuid import uuid4, UUID
from typing import Any, Dict, List
import mysql.connector
import json

router = APIRouter()

def get_db_connection():
    try:
        return mysql.connector.connect(
            host="data-db-1",
            port=3306,
            user="user",
            password="password",
            database="appdb"
        )
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# Create
@router.post("/", response_model=ApplicationResponse)
async def create_application(request: GeneralApplicationRequest):
    app_id = str(uuid4())
    if request.application_type == ApplicationType.dns:
        try:
            dns_form = dnsApplicationForm(**request.additionForm)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid DNS form: {str(e)}")
        # Save data to DB
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            query = """
            INSERT INTO applications (id, type, base_form, extra_form)
            VALUES (%s, %s, %s, %s)
            """
            values = (
                app_id,
                request.application_type.value,
                request.baseForm.json(), 
                dns_form.json() 
            )
            cursor.execute(query, values)
            conn.commit()
        except mysql.connector.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    else:
        raise HTTPException(status_code=400, detail="Unsupported application type")

    return {
        "application_id": app_id,
        "message": f"Thanks for your {request.application_type.value} apply!"
    }

# Read all
@router.get("/getAll", response_model=Dict[str, Dict[str, Any]])
async def get_all_applications():
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, type, base_form, extra_form FROM applications"
        cursor.execute(query)
        results = cursor.fetchall()
        
        applications = {}
        for row in results:
            applications[row["id"]] = {
                "type": row["type"],
                "base": json.loads(row["base_form"]),
                "extra": json.loads(row["extra_form"]) if row["extra_form"] else None
            }
        
        count = len(results)
        print(f"Retrieved {count} applications from database")
        
        return applications
    
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Get application by student ID
@router.get("/my-applications", response_model=List[Dict[str, Any]])
async def get_applications_by_user(request: Request):
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT id, type, base_form, extra_form 
            FROM applications 
            WHERE JSON_UNQUOTE(JSON_EXTRACT(base_form, '$.applicant_account')) = %s
        """
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()

        if not rows:
            return []

        results = []
        for row in rows:
            results.append({
                "application_id": row["id"],
                "type": row["type"],
                "base": json.loads(row["base_form"]) if row["base_form"] else None,
                "extra": json.loads(row["extra_form"]) if row["extra_form"] else None
            })

        return results

    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Read by application ID
@router.get("/{application_id}", response_model=Dict[str, Any])
async def get_application(application_id: str):
    print("GET application_id:", application_id)
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, type, base_form, extra_form FROM applications WHERE id = %s"
        cursor.execute(query, (application_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Application not found")

        return {
            "type": row["type"],
            "base": json.loads(row["base_form"]) if row["base_form"] else None,
            "extra": json.loads(row["extra_form"]) if row["extra_form"] else None
        }

    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()



# Update by application ID
@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(application_id: str, updated_data: GeneralApplicationRequest):
    if updated_data.application_type != ApplicationType.dns:
        raise HTTPException(status_code=400, detail="Unsupported application type")

    try:
        dns_form = dnsApplicationForm(**updated_data.additionForm)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid DNS form: {str(e)}")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            UPDATE applications
            SET type=%s, base_form=%s, extra_form=%s
            WHERE id=%s
        """
        values = (
            updated_data.application_type.value,
            updated_data.baseForm.json(),
            dns_form.json(),
            application_id
        )
        cursor.execute(query, values)
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Application not found")

    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return {
        "application_id": application_id,
        "message": "Application updated successfully"
    }

@router.put("/cancel/{application_id}", response_model=ApplicationResponse)
async def cancel_application(application_id: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            UPDATE applications
            SET base_form = JSON_SET(base_form, '$.status', %s)
            WHERE id = %s
        """
        values = (ApplicationStatus.canceled.value, application_id)

        cursor.execute(query, values)
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Application not found")

    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return {
        "application_id": application_id,
        "message": "Application canceled successfully"
    }

# Delete by application ID
@router.delete("/{application_id}", response_model=ApplicationResponse)
async def delete_application(application_id: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "DELETE FROM applications WHERE id = %s"
        cursor.execute(query, (application_id,))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Application not found")

    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return {
        "application_id": application_id,
        "message": "Application deleted successfully"
    }



