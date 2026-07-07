"""
Data models for CIS Benchmarks and Controls.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.models.user import PyObjectId

class BenchmarkControlModel(BaseModel):
    """
    Definition of an individual CIS Benchmark rule/control.
    """
    control_id: str
    control_name: str
    description: str
    category: str
    severity: str  # critical, high, medium, low, informational
    expected_value: str
    check_command: str  # Bash command or PowerShell script block
    remediation: str
    remediation_command: Optional[str] = None
    references: List[str] = Field(default_factory=list)
    impact: Optional[str] = None
    platform: str  # linux, windows

class BenchmarkModel(BaseModel):
    """
    Represents a full CIS Benchmark catalog (e.g. Ubuntu 22.04, Windows 11).
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    short_name: str  # e.g., ubuntu_22, windows_11
    version: str = "1.0.0"
    platform: str  # linux, windows
    os_family: str  # ubuntu, windows, rhel, debian, etc.
    description: str
    total_controls: int
    controls: List[BenchmarkControlModel] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "name": "CIS Ubuntu Linux 22.04 LTS Benchmark",
                "short_name": "ubuntu_22",
                "version": "1.0.0",
                "platform": "linux",
                "os_family": "ubuntu",
                "description": "Center for Internet Security (CIS) Benchmark for Ubuntu Linux 22.04 LTS.",
                "total_controls": 45,
                "controls": []
            }
        }
