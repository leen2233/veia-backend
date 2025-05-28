from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt

from conf import SECRET_KEY
from lib.db import User

ALGORITHM = "HS256"
EXP_MINUTES = 60


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def check_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_tokens(user: User) -> dict:
    access_payload = {"sub": str(user._id), "exp": datetime.utcnow() + timedelta(minutes=15), "type": "access"}
    refresh_payload = {"sub": str(user._id), "exp": datetime.utcnow() + timedelta(days=7), "type": "refresh"}
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access": access_token, "refresh": refresh_token}


def refresh_access_token(refresh_token: str) -> Optional[str]:
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        new_payload = {"sub": payload["sub"], "exp": datetime.utcnow() + timedelta(minutes=15), "type": "access"}
        return jwt.encode(new_payload, SECRET_KEY, algorithm=ALGORITHM)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def validate_access_token(token: str) -> Optional[dict]:
    """
    Validate access token and return payload if valid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        if datetime.utcnow().timestamp() > payload.get("exp", 0):
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
