"""
Data model for real-time and persistent user notifications.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from app.models.user import PyObjectId

class NotificationModel(BaseModel):
    """
    Represents an event alert or system notification pushed to a user.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str  # recipient user id, or "all" for global broadcast
    type: str  # audit_started, audit_completed, audit_failed, system_added, system_offline, critical_finding
    title: str
    message: str
    severity: str = "info"  # info, warning, error, success
    is_read: bool = False
    link: Optional[str] = None  # UI page route to link to
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "user_id": "user_id_string",
                "type": "audit_completed",
                "title": "Audit Completed",
                "message": "CIS compliance audit finished for system prod-web-01 with score 84.5%",
                "severity": "success",
                "is_read": False,
                "link": "/audits/64b5f8ca2b036574f1b80f12"
            }
        }
