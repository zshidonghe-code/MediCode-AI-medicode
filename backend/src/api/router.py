from fastapi import APIRouter
from src.api.v1.endpoints import coding, drg, qc, dashboard, auth, admin, pipeline, rejection

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(coding.router, prefix="/coding", tags=["编码"])
api_router.include_router(drg.router, prefix="/drg", tags=["DRG分组"])
api_router.include_router(qc.router, prefix="/qc", tags=["质控"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["数据看板"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理"])
api_router.include_router(pipeline.router, prefix="/pipeline", tags=["流水线"])
api_router.include_router(rejection.router, prefix="/rejection", tags=["医保拒付预测"])
