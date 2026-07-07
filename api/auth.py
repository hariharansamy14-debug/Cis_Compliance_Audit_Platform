"""
Concept: Authentication API Routes
Why it's needed: The frontend needs specific URLs (endpoints) to send registration data and login credentials.
How it works: We use FastAPI's `APIRouter` to group related routes.

Code Explanation:
- `/register`: Takes user data, validates, sends OTP via email, saves to MongoDB.
- `/verify-otp`: Verifies OTP and marks email as verified.
- `/resend-otp`: Resends OTP to registered email.
- `/login`: Verifies credentials and returns JWT token.
- `/me`: Protected route returning logged-in user profile.
"""

from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.authentication.hash import get_password_hash, verify_password
from app.authentication.jwt import create_access_token, get_current_user
from app.database.connection import get_database
from app.models.user import UserModel
from app.schemas.user import UserCreate, UserResponse, OTPVerification, ResendOTP
from app.security.email_otp import create_otp_token, send_verification_email, verify_otp

router = APIRouter()


def serialize_mongo_doc(document: dict[str, Any] | None) -> dict[str, Any] | None:
    """Convert MongoDB document values to JSON-safe Python types for FastAPI responses."""
    if not document:
        return None

    serialized = dict(document)
    if "_id" in serialized:
        serialized["id"] = str(serialized["_id"])
        serialized.pop("_id", None)

    for key, value in list(serialized.items()):
        if isinstance(value, ObjectId):
            serialized[key] = str(value)

    return serialized


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Any = Depends(get_database)):
    """Register a new user and send OTP via email.
    
    Process:
    1. Validates email and username
    2. Creates user with is_email_verified=False
    3. Generates OTP and sends via email
    4. Returns user data (email not yet verified)
    
    Validates:
    - Email is valid format
    - Username doesn't already exist
    - Email doesn't already exist
    - Password is at least 8 characters
    """
    if len(user.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

    # Check for existing email or username (case-insensitive for email)
    existing_user = await db["users"].find_one({
        "$or": [
            {"email": user.email.lower()},
            {"username": user.username}
        ]
    })
    if existing_user:
        if existing_user.get("email", "").lower() == user.email.lower():
            raise HTTPException(status_code=400, detail="Email already registered")
        else:
            raise HTTPException(status_code=400, detail="Username already exists")

    # Generate OTP
    otp_code, otp_expiration = create_otp_token()
    
    # Send verification email
    email_sent = send_verification_email(user.email, otp_code, user.username)
    if not email_sent:
        raise HTTPException(
            status_code=500,
            detail="Failed to send verification email. Please try again later."
        )

    # Hash password and create user
    hashed_password = get_password_hash(user.password)
    user_dict = user.model_dump()
    user_dict["hashed_password"] = hashed_password
    user_dict["email"] = user_dict["email"].lower()
    user_dict["otp_code"] = otp_code
    user_dict["otp_expiration"] = otp_expiration
    user_dict["is_email_verified"] = False
    del user_dict["password"]

    db_user = UserModel(**user_dict)
    result = await db["users"].insert_one(db_user.model_dump(by_alias=True, exclude={"id"}))

    created_user = await db["users"].find_one({"_id": result.inserted_id})
    return {
        "message": "Registration successful. Please check your email for verification code.",
        "user": serialize_mongo_doc(created_user)
    }


@router.post("/verify-otp")
async def verify_email_otp(verification: OTPVerification, current_user: dict = Depends(get_current_user), db: Any = Depends(get_database)):
    """Verify OTP and mark email as verified.
    
    Requires:
    - User must be logged in (JWT token required)
    - OTP must be 6 digits
    - OTP must match and not be expired
    """
    # Get user from database
    user = await db["users"].find_one({"_id": current_user.get("_id")})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("is_email_verified"):
        raise HTTPException(status_code=400, detail="Email is already verified")
    
    # Verify OTP
    if not verify_otp(verification.otp_code, user.get("otp_code", ""), user.get("otp_expiration")):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP code")
    
    # Mark email as verified and clear OTP
    await db["users"].update_one(
        {"_id": current_user.get("_id")},
        {"$set": {
            "is_email_verified": True,
            "otp_code": None,
            "otp_expiration": None
        }}
    )
    
    # Get updated user
    updated_user = await db["users"].find_one({"_id": current_user.get("_id")})
    
    return {"message": "Email verified successfully!", "user": serialize_mongo_doc(updated_user)}


@router.post("/resend-otp")
async def resend_otp(request: ResendOTP, db: Any = Depends(get_database)):
    """Resend OTP to user's email.
    
    Allows users to request a new OTP if the previous one expired.
    """
    # Find user by email
    user = await db["users"].find_one({"email": request.email.lower()})
    
    if not user:
        # Don't reveal if email exists (security best practice)
        return {"message": "If the email is registered, a new verification code will be sent."}
    
    if user.get("is_email_verified"):
        return {"message": "Email is already verified. You can login now."}
    
    # Generate new OTP
    otp_code, otp_expiration = create_otp_token()
    
    # Send verification email
    email_sent = send_verification_email(request.email, otp_code, user.get("username"))
    if not email_sent:
        raise HTTPException(
            status_code=500,
            detail="Failed to send verification email. Please try again later."
        )
    
    # Update OTP in database
    await db["users"].update_one(
        {"email": request.email.lower()},
        {"$set": {
            "otp_code": otp_code,
            "otp_expiration": otp_expiration
        }}
    )
    
    return {"message": "Verification code has been sent to your email."}


@router.post("/login")
async def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Any = Depends(get_database)):
    """Authenticate a user with username or email and return a JWT.
    
    The 'username' field in OAuth2PasswordRequestForm can accept:
    - Username (e.g., 'johndoe')
    - Email (e.g., 'johndoe@example.com')
    
    Note: Users can login even if email is not verified yet.
    Email verification is recommended but not enforced.
    """
    # Try to find user by username first, then by email
    identifier = user_credentials.username
    user = await db["users"].find_one({"username": identifier})
    
    # If not found by username, try email (case-insensitive)
    if not user:
        user = await db["users"].find_one({"email": identifier.lower()})
    
    if not user or not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user["_id"])})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Get current logged in user's profile."""
    return current_user
