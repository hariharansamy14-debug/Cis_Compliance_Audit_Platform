"""
Concept: JWT Authentication (JSON Web Tokens)
Why it's needed: HTTP is stateless. After a user logs in, the server needs a way to remember who they are for subsequent requests (like viewing a dashboard).
How it works: Upon successful login, the server creates a token (JWT) containing the user's ID and signs it with a secret key. The frontend stores this token and sends it with every request. The backend verifies the signature to authenticate the user.

Code Explanation:
- `create_access_token()`: Generates a JWT containing the user's data (`sub`) and an expiration time (`exp`).
- `get_current_user()`: A FastAPI dependency. It intercepts incoming requests, extracts the JWT from the Authorization header, decodes it, and fetches the user from the database. If invalid, it throws an error.
"""

from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from app.config import settings
from app.database.connection import get_database
from bson import ObjectId

# OAuth2 setup: Tells FastAPI where the frontend will send login requests to get a token.
# (This is mostly for the auto-generated Swagger UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates a signed JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    # Add expiration to payload
    to_encode.update({"exp": expire})
    
    # Sign the token using our secret key and algorithm
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_database)):
    """
    Dependency to get the currently logged in user based on their JWT.
    Protects routes from unauthorized access.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the token
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # Fetch user from database
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise credentials_exception
        
    # Convert _id to string id for our schema
    user['id'] = str(user['_id'])
    return user
