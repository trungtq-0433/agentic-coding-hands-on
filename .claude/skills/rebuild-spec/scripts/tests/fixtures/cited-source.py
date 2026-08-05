# cited-source.py — synthetic source file for citation validator tests.
# Lines 5-10 are deliberately inside bounds for spec-pass.md citation.

def authenticate(email: str, password: str) -> bool:
    """Validate user credentials against the database."""
    user = find_user_by_email(email)
    if user is None:
        return False
    return verify_password(password, user.password_hash)


def find_user_by_email(email: str):
    """Look up a user record by email address."""
    # In production this queries the users table.
    return None


def verify_password(plain: str, hashed: str) -> bool:
    """Compare a plaintext password against a bcrypt hash."""
    import hashlib
    return hashlib.sha256(plain.encode()).hexdigest() == hashed


def create_session(user_id: int) -> str:
    """Generate a random session token and persist it."""
    import secrets
    token = secrets.token_hex(64)
    # INSERT INTO sessions (user_id, token, expires_at) VALUES (...)
    return token


def revoke_session(token: str) -> None:
    """Delete a session record by token."""
    # DELETE FROM sessions WHERE token = ?
    pass
