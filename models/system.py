"""
Database model for audited Systems.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from app.models.user import PyObjectId

class SystemModel(BaseModel):
    """
    Represents an IT asset (Server, Workstation, VM) audited for CIS compliance.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    hostname: str
    ip_address: str
    operating_system: str  # ubuntu, windows_11, rhel, debian, rocky, centos, windows_server, amazon_linux
    os_version: Optional[str] = None
    department: Optional[str] = None
    owner: str  # user id of the registered owner/creator
    location: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    status: str = "active"  # active, inactive, maintenance, offline
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_audit_date: Optional[datetime] = None
    last_audit_score: Optional[float] = None
    audit_frequency: str = "monthly"  # daily, weekly, monthly, quarterly
    connection_type: str = "agent"  # ssh, winrm, agent
    
    # Credentials/Port configuration for Remote Audits
    ssh_port: int = 22
    ssh_username: Optional[str] = None
    winrm_port: int = 5985
    notes: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "hostname": "prod-web-01",
                "ip_address": "192.168.1.50",
                "operating_system": "ubuntu",
                "os_version": "22.04 LTS",
                "department": "IT Operations",
                "owner": "user_id_string",
                "location": "AWS us-east-1",
                "tags": ["production", "web"],
                "status": "active",
                "audit_frequency": "weekly",
                "connection_type": "ssh",
                "ssh_port": 22,
                "ssh_username": "ubuntu"
            }
        }
