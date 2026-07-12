from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.auth import SignupRequest, SignupResponse
from app.services.auth_service import AuthService

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
    """Receives user payload, registers client credentials, and initiates database mapping."""
    auth_service = AuthService(db)
    new_user = auth_service.register_user(data)
    
    return SignupResponse(
        message="User account created and profile synchronized successfully.",
        user_id=new_user.id
    )