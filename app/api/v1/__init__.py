from fastapi import APIRouter
from app.api.v1.sosmed import router as sosmed_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(sosmed_router)
