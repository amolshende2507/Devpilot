from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
        description="User full name"
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        description="Password must be at least 8 characters"
    )

    
class SignupResponse(BaseModel):

    message: str

    user_id: str