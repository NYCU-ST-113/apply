from fastapi import FastAPI
from routers import apply

app = FastAPI(title="Apply Service")

app.include_router(apply.router, prefix="/api/apply", tags=["Apply"])
