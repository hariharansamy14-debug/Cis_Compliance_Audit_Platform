"""
Data model for audit trail activity logging.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from app.models.user import PyObjectId

class ActivityLogModel(BaseModel):
    """
    Audit log of administrative or security actions taken within the platform.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: Optional[str] = None  # user ID who initiated, or None for system
    action: str  # login, logout, audit_run, system_create, report_download, etc.
    resource_type: Optional[str] = None  # system, audit, user, report
    resource_id: Optional[str] = None
    details: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "user_id": "user_id_string",
                "action": "system_create",
                "resource_type": "system",
                "resource_id": "system_id_string",
                "details": "Registered new system prod-web-01 with IP 192.168.1.50",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0..."
            }
        }
