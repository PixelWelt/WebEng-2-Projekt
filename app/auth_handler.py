import jwt
from datetime import datetime, timedelta
from fastapi import Request

SECRET_KEY = "your_secret_key"

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    """Creates a JWT access token with an expiration time.
    args:
        data (dict): The data to encode in the token.
        expires_delta (timedelta): The duration after which the token expires.
    returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

def verify_access_token(request: Request):
    """
    Verifies the JWT access token from the request cookies.
    args:
        request (Request): The FastAPI request object containing cookies.
    returns:
        dict or None: The decoded token payload if valid, None if invalid or expired.
    """
    token = request.cookies.get("access_token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

