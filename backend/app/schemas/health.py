from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class SystemMetrics(BaseModel):
    ram_total_gb: Optional[float] = None
    ram_available_gb: Optional[float] = None
    disk_free_gb: Optional[float] = None

class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Application operational status")
    project: str = Field(..., description="Project name")
    version: str = Field(..., description="Application semantic version")
    database_connected: bool = Field(..., description="SQLAlchemy SQLite connectivity status")
    vector_db_path: str = Field(..., description="Configured Qdrant persistent directory")
    system_metrics: SystemMetrics
