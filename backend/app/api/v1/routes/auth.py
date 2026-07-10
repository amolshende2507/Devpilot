from fastapi import APIRouter, Depends

from app.core.security import verify_token


# router = APIRouter()

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)
# @router.get("/me")
# def get_me(
#     user=Depends(verify_token)
# ):

#     return {
#         "message":"Authenticated",

#         "user":user
#     }
