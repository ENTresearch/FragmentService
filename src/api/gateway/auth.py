from typing import Optional
from fastapi import Header, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
import os
import httpx

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
API_KEY_SECRET = os.getenv('API_KEY_SECRET')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_api_key(api_key: Optional[str] = Header(None, alias="apikey")):
    """API key verification (in header)"""

    try:
        return jwt.decode(api_key, API_KEY_SECRET, algorithms=["HS256"])
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="API key expired")
    except jwt.exceptions.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid API key")

def verify_jwt(token: str = Depends(oauth2_scheme)):
    """JWT token verification through decoding"""
    try:
        return jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

async def verify_jwt_online(token: str = Depends(oauth2_scheme)):
    """JWT token verification via Supabase"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SUPABASE_URL}/auth/v1/user", headers={
            "Authorization": f"Bearer {token}",
            "apikey": SUPABASE_KEY,
        })
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Unauthorized user")
        return response.json()
    
def verify_admin_jwt(token: str = Depends(oauth2_scheme)):
    """Check if user has admin role while verifying the token validity"""
    user = verify_jwt(token)
    if user.get('app_metadata', {}).get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user

def verify_admin_api_key(api_key: Optional[str] = Header(None, alias="apikey")):
    """Check if user has admin role while verifying the api key validity"""
    decoded = verify_api_key(api_key)
    
    if decoded.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return decoded
