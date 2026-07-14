from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.supabase import supabase

security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verifies the inbound JWT token using the official Supabase Auth validation engine."""
    token = credentials.credentials

    try:
        # Pass token directly to the official authentication service engine.
        # This checks signatures, validation, and account status in one operation.
        auth_response = supabase.auth.get_user(token)
        
        user = auth_response.user
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed: Valid session not found."
            )

        # Map Supabase User parameters into our unified application payload context
        return {
            "sub": user.id,
            "email": user.email,
            "role": user.role if user.role else "authenticated"
        }

    except Exception as e:
        # Safely catch signature mismatch, token expiry, and account locks
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired credentials: {str(e)}"
        )