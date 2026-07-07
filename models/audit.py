"""
Data models for Audit Results.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.models.user import PyObjectId

class ControlResult(BaseModel):
    """
    Result of an individual CIS benchmark control check.
    """
    control_id: str
    control_name: str
    description: str
    category: str
    severity: str  # critical, high, medium, low, informational
    expected_value: str
    actual_value: str
    status: str  # passed, failed, error, not_applicable
    evidence: str
    remediation: str
    remediation_command: Optional[str] = None
    references: List[str] = Field(default_factory=list)
    impact: Optional[str] = None

class AuditResultModel(BaseModel):
    """
    Complete audit execution report detailing compliance metrics.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    system_id: str
    benchmark_id: str
    benchmark_version: str = "1.0.0"
    audit_date: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: str = "pending"  # pending, running, completed, failed, cancelled
    run_by: str  # User ID who triggered the audit
    compliance_score: float = 0.0  # Percentage (0 - 100)
    risk_score: float = 0.0  # Enterprise risk score (0 - 100)
    
    # Check status counters
    total_controls: int = 0
    passed_controls: int = 0
    failed_controls: int = 0
    error_controls: int = 0
    not_applicable_controls: int = 0
    
    # Severity breakdown of failures
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    
    results: List[ControlResult] = Field(default_factory=list)
    system_info: Dict[str, Any] = Field(default_factory=dict)
    report_path: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "system_id": "system_id_string",
                "benchmark_id": "ubuntu_22",
                "benchmark_version": "1.0.0",
                "status": "completed",
                "run_by": "user_id_string",
                "compliance_score": 85.5,
                "risk_score": 12.0,
                "total_controls": 40,
                "passed_controls": 34,
                "failed_controls": 6,
                "error_controls": 0,
                "not_applicable_controls": 0,
                "results": []
            }
        }
