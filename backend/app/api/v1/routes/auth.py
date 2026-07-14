from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.auth import SignupRequest, SignupResponse, LoginRequest, TokenResponse
from app.services.auth_service import AuthService
from app.core.security import verify_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/signup", 
    response_model=SignupResponse, 
    status_code=status.HTTP_201_CREATED
)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    new_user = auth_service.register_user(data)
    return SignupResponse(
        message="User account created and profile synchronized successfully.",
        user_id=new_user.id
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK
)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Validates login credentials and issues a secure JWT bearer token."""
    auth_service = AuthService(db)
    token_data = auth_service.login_user(data)
    return token_data


@router.get(
    "/me",
    status_code=status.HTTP_200_OK
)
def get_current_user(user_payload: dict = Depends(verify_token)):
    """A protected endpoint that returns the decoded JWT user metadata context.
    
    This route requires an 'Authorization: Bearer <JWT_TOKEN>' header.
    """
    return {
        "authenticated": True,
        "user_id": user_payload.get("sub"),
        "email": user_payload.get("email"),
        "role": user_payload.get("role")
    }