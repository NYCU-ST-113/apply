from pydantic import BaseModel, EmailStr
from enum import Enum

class ApplicationStatus(str, Enum):
    pending = "Pending"
    under_review = "Under Review"
    approved = "Approved"
    rejected = "Rejected"
    completed = "Completed"
    canceled = "Canceled"

class ApplicationType(str, Enum):
    dns = "DNS" # DNS domain apply
    office = "Office" # Office apply


class ApplicationForm(BaseModel): # Basic application
    department: str
    applicant_account: str
    applicant_name: str
    applicant_phone: str
    applicant_email: EmailStr

    tech_contact_name: str
    tech_contact_phone: str
    tech_contact_email: EmailStr
    supervisor_name: str
    supervisor_id: str
    supervisor_email: EmailStr
    apply_date: str

    status: ApplicationStatus = ApplicationStatus.pending

class GeneralApplicationRequest(BaseModel):
    application_type: ApplicationType # e.g. DNS, Office
    baseForm: ApplicationForm
    additionForm: dict 

class ApplicationResponse(BaseModel):
    application_id: str
    message: str

class dnsApplicationForm(BaseModel):
    applicant_unit: str
    domain_name: str
    application_project: str
    dns_manage_account: str
    reason: str




    
