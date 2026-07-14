from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.supabase import supabase
from app.repositories.user_repository import UserRepository
from app.schemas.auth import SignupRequest, LoginRequest


class AuthService:
    def __init__(self, db: Session):
        """Inject user repository dependency connected to local DB."""
        self.user_repo = UserRepository(db)

    def register_user(self, data: SignupRequest):
        """Orchestrates user creation across Supabase Auth and PostgreSQL database."""
        # Check if email is already taken in our DB
        existing_user = self.user_repo.get_by_email(data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists."
            )

        # Register the user via Supabase Auth Client
        try:
            auth_response = supabase.auth.sign_up({
                "email": data.email,
                "password": data.password,
                "options": {
                    "data": {
                        "name": data.name
                    }
                }
            })
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Authentication service registration failed: {str(e)}"
            )

        # Validate response payload structure
        if not auth_response.user or not auth_response.user.id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User registered in Auth server, but no valid identifier was returned."
            )

        user_uuid = auth_response.user.id

        # Mirror identity to local database profile
        try:
            db_user = self.user_repo.create_user(user_id=user_uuid, data=data)
            return db_user
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to create public.users profile for UUID {user_uuid}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Account created but profile synchronization failed. Please contact support."
            )

    def login_user(self, data: LoginRequest):
        """Authenticates user credentials against Supabase and returns session tokens."""
        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": data.email,
                "password": data.password
            })
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed: Invalid credentials or unverified account."
            )

        if not auth_response.session or not auth_response.session.access_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication server failed to generate a session token."
            )

        return {
            "access_token": auth_response.session.access_token,
            "token_type": "bearer"
        }