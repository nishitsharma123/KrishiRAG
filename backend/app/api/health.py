import os
import shutil
import ctypes
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.session import get_db
from backend.app.schemas.health import HealthResponse, SystemMetrics

router = APIRouter(tags=["Health & Diagnostics"])

def get_system_metrics() -> SystemMetrics:
    ram_total = None
    ram_avail = None
    disk_free = None

    try:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            ram_total = round(stat.ullTotalPhys / (1024**3), 2)
            ram_avail = round(stat.ullAvailPhys / (1024**3), 2)
    except Exception as e:
        logger.warning(f"Could not read RAM metrics: {e}")

    try:
        _, _, free = shutil.disk_usage(settings.STORAGE_PATH if os.path.exists(settings.STORAGE_PATH) else ".")
        disk_free = round(free / (1024**3), 2)
    except Exception as e:
        logger.warning(f"Could not read disk metrics: {e}")

    return SystemMetrics(
        ram_total_gb=ram_total,
        ram_available_gb=ram_avail,
        disk_free_gb=disk_free
    )

@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def check_health(db: Session = Depends(get_db)):
    """
    Primary health diagnostic endpoint.
    Verifies SQLite database connectivity, vector storage directory configuration, and host hardware metrics.
    """
    db_connected = False
    try:
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            db_connected = True
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}")
        db_connected = False

    metrics = get_system_metrics()

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        project=settings.PROJECT_NAME,
        version=settings.VERSION,
        database_connected=db_connected,
        vector_db_path=settings.QDRANT_STORAGE_PATH,
        system_metrics=metrics
    )
