"""
Data models for User details.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    """
    Custom type to handle MongoDB's ObjectIds in Pydantic.
    MongoDB uses `_id` of type ObjectId, but we want to represent it as a string in our API.
    """
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.str_schema()
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(str)
        )

class UserModel(BaseModel):
    """
    The internal representation of a User in the database.
    Extended to include roles, active state, profiles, and refresh tokens.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    email: EmailStr
    hashed_password: str
    role: str = "viewer"  # administrator, security_analyst, auditor, viewer
    department: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    is_email_verified: bool = False
    otp_code: Optional[str] = None
    otp_expiration: Optional[datetime] = None
    refresh_token_hash: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "username": "admin",
                "email": "admin@example.com",
                "hashed_password": "hashed_secret_password",
                "role": "administrator",
                "department": "Security Operations",
                "first_name": "Admin",
                "last_name": "User",
                "is_active": True,
                "is_email_verified": True
            }
        }
