"""
Role-Based Access Control (RBAC) definitions and dependencies.
"""

from typing import List, Set
from enum import Enum
from fastapi import Depends, HTTPException, status
from app.core.security import get_current_active_user

class SystemRole(str, Enum):
    ADMINISTRATOR = "administrator"
    SECURITY_ANALYST = "security_analyst"
    AUDITOR = "auditor"
    VIEWER = "viewer"

# Standardizing DB role naming formats
ROLE_MAPPING = {
    "admin": SystemRole.ADMINISTRATOR,
    "administrator": SystemRole.ADMINISTRATOR,
    "security analyst": SystemRole.SECURITY_ANALYST,
    "security_analyst": SystemRole.SECURITY_ANALYST,
    "auditor": SystemRole.AUDITOR,
    "viewer": SystemRole.VIEWER,
    "user": SystemRole.VIEWER
}

# Permissions mapping per role
PERMISSIONS = {
    SystemRole.ADMINISTRATOR: {"*"},
    SystemRole.SECURITY_ANALYST: {
        "systems.read", "systems.create", "systems.update", "systems.delete",
        "audits.read", "audits.run", "audits.delete",
        "reports.read", "reports.create", "reports.delete",
        "benchmarks.read", "benchmarks.manage",
        "notifications.read", "notifications.manage",
        "dashboard.read", "users.read"
    },
    SystemRole.AUDITOR: {
        "systems.read",
        "audits.read", "audits.run",
        "reports.read", "reports.create",
        "benchmarks.read",
        "notifications.read",
        "dashboard.read"
    },
    SystemRole.VIEWER: {
        "systems.read",
        "audits.read",
        "reports.read",
        "benchmarks.read",
        "notifications.read",
        "dashboard.read"
    }
}

def get_user_role(role_str: str) -> SystemRole:
    """Normalize and match user role string to SystemRole enum."""
    if not role_str:
        return SystemRole.VIEWER
    normalized = role_str.strip().lower()
    return ROLE_MAPPING.get(normalized, SystemRole.VIEWER)

def has_permission(user_role_str: str, permission: str) -> bool:
    """Check if a user role has the required permission."""
    role = get_user_role(user_role_str)
    role_perms = PERMISSIONS.get(role, set())
    if "*" in role_perms:
        return True
    
    # Check for prefix match e.g. systems.* matches systems.read
    if permission in role_perms:
        return True
        
    prefix = permission.split(".")[0] + ".*"
    if prefix in role_perms:
        return True
        
    return False

def require_role(allowed_roles: List[str]):
    """FastAPI dependency to enforce one of the specified roles."""
    async def dependency(current_user: dict = Depends(get_current_active_user)):
        user_role = current_user.get("role", "viewer")
        normalized_user_role = get_user_role(user_role).value
        normalized_allowed = [get_user_role(r).value for r in allowed_roles]
        
        # Admin overrides all role checks
        if normalized_user_role == SystemRole.ADMINISTRATOR.value:
            return current_user
            
        if normalized_user_role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required role to access this resource"
            )
        return current_user
    return dependency

def require_permission(permission: str):
    """FastAPI dependency to enforce a specific permission."""
    async def dependency(current_user: dict = Depends(get_current_active_user)):
        user_role = current_user.get("role", "viewer")
        if not has_permission(user_role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have the required permission: {permission}"
            )
        return current_user
    return dependency
