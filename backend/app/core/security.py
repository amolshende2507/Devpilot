from fastapi import HTTPException, Depends

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from jose import jwt, JWTError

from app.core.config import settings



security = HTTPBearer()



def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials


    try:

        payload = jwt.decode(

            token,

            settings.SUPABASE_JWT_SECRET,

            algorithms=["HS256"]

        )


        return payload


    except JWTError:


        raise HTTPException(

            status_code=401,

            detail="Invalid authentication token"

        )