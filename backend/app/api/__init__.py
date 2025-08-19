from fastapi import APIRouter
from .uploads import router as uploads_router
from .query import router as query_router
from .dashboard import router as dashboard_router

router = APIRouter()
router.include_router(uploads_router)
router.include_router(query_router)
router.include_router(dashboard_router)