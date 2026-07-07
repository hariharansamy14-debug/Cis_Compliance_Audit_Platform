"""
Concept: Password Hashing
Why it's needed: Storing passwords in plain text is a massive security risk. If a database is breached, attackers get everyone's passwords. Hashing turns a password into an irreversible string.
How it works: We use `bcrypt`, a proven hashing algorithm. When a user registers, we hash the password. When they log in, we hash the provided password and compare it to the stored hash.

Code Explanation:
- `pwd_context`: Initializes the Passlib context with bcrypt.
- `verify_password()`: Checks if a plain password matches a hashed password.
- `get_password_hash()`: Generates a hash from a plain password.
"""

import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed one."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash of a password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
