from fastapi import APIRouter, HTTPException
from models import ApplicationForm, ApplicationType, GeneralApplicationRequest, ApplicationResponse, dnsApplicationForm, ApplicationStatus
from uuid import uuid4, UUID
from typing import Any, Dict

router = APIRouter()

# TODO: Simulate database
# db: Dict[str, GeneralApplicationRequest] = {}
db: Dict[str, Dict[str, Any]] = {}

# 生成範例 ApplicationForm
base_form = ApplicationForm(
    department="資訊工程系",
    applicant_account="b112345678",
    applicant_name="王小明",
    applicant_phone="0912345678",
    applicant_email="b112345678@nycu.edu.tw",
    tech_contact_name="張工程師",
    tech_contact_phone="0922333444",
    tech_contact_email="tech@nycu.edu.tw",
    supervisor_name="林教授",
    supervisor_id="A123456789",
    supervisor_email="lin@nycu.edu.tw",
    apply_date="2025-05-10",
    status=ApplicationStatus.pending
)

# 生成範例 dnsApplicationForm
dns_form = dnsApplicationForm(
    applicant_unit="資工系實驗室",
    domain_name="lab.cs.nycu.edu.tw",
    application_project="網路測試平台",
    dns_manage_account="dnsadmin",
    reason="研究用途"
)

# 模擬 app_id 並填入 db
app_id = str(uuid4())
db[app_id] = {
    "type": "dns",
    "base": base_form,
    "extra": dns_form
}

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
        db[app_id] = {
            "type": request.application_type,
            "base": request.baseForm,
            "extra": dns_form
        }

    # elif request.application_type == ApplicationType.office:
    #     try:
    #         office_form = dnsApplicationForm(**request.additionForm)
    #     except Exception as e:
    #         raise HTTPException(status_code=400, detail=f"Invalid DNS form: {str(e)}")
        
    #     db[app_id] = {
    #         "type": request.application_type,
    #         "base": request.baseForm,
    #         "extra": dns_form
    #     }
    else:
        raise HTTPException(status_code=400, detail="Unsupported application type")

    return {
        "application_id": app_id,
        "message": f"Thanks for your {request.application_type.value} apply!"
    }
# Create with JWT verification
# @router.post("/", response_model=ApplicationResponse)
# async def create_application(request: dnsApplicationRequest, token_data: dict = Depends(verify_jwt_token)):
#     app_id = str(uuid4())
#     db[app_id] = request.baseForm
#     return {
#         "application_id": app_id,
#         "message": f"Thanks {token_data['name']} for your apply, we will send email to {request.baseForm.applicant_email}"
#     }

# Read
@router.get("/", response_model=Dict[str, Dict[str, Any]])
async def get_all_applications():
    return db

# Read by application ID
@router.get("/{application_id}", response_model=ApplicationForm)
async def get_application(application_id: str):
    if application_id not in db:
        raise HTTPException(status_code=404, detail="Application not found")
    return db[application_id]

# Update by application ID
@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(application_id: str, updated_data: ApplicationForm):
    if application_id not in db:
        raise HTTPException(status_code=404, detail="Application not found")
    db[application_id] = updated_data
    return {
        "application_id": application_id,
        "message": "Application updated successfully"
    }

# Delete by application ID
@router.delete("/{application_id}", response_model=ApplicationResponse)
async def delete_application(application_id: str):
    if application_id not in db:
        raise HTTPException(status_code=404, detail="Application not found")
    del db[application_id]
    return {
        "application_id": application_id,
        "message": "Application deleted successfully"
    }

# @router.get("/sample", response_model=ApplicationForm)
# async def get_sample_application():
#     return ApplicationForm(
#         department="資訊工程系",
#         applicant_account="b112345678",
#         applicant_name="小明",
#         applicant_phone="0912345678",
#         applicant_email="b112345678@gs.ncku.edu.tw",
#         tech_contact_name="技術人員小華",
#         tech_contact_phone="0922333444",
#         tech_contact_email="tech@example.com",
#         supervisor_name="指導教授小林",
#         supervisor_id="F123456789",
#         supervisor_email="supervisor@ncku.edu.tw"
#     )


PAYMENT_SERVICE_URL = "http://payment_service:8001/payment"

# Approve the apply
# @app.put("/apply/{application_id}/approve")
# async def approve_application(application_id: str):
#     # Check the spplication ID
#     application = fake_db.get(application_id)
#     if not application:
#         raise HTTPException(status_code=404, detail="Application not found")

#     # The apply is pending
#     if application["status"] != ApplicationStatus.pending:
#         raise HTTPException(status_code=400, detail="Application is not pending")

#     # Update to approved
#     application["status"] = ApplicationStatus.approved

#     # TODO: Start payment

# Payment request
# async def initiate_payment(application):
#     async with httpx.AsyncClient() as client:
#         payment_data = {
#             "application_id": application["application_id"],
#             "amount": 100, 
#         }
#         response = await client.post(PAYMENT_SERVICE_URL, json=payment_data)

#         if response.status_code == 200:
#             return response.json() 
#         else:
#             raise Exception("Failed to communicate with payment service")


