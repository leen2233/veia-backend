from dataclasses import dataclass
from typing import Callable, Dict

from lib import db
from lib.connection import Connection
from utils import crypt
from utils.decorators import protected


@dataclass
class Response:
    status: bool
    data: Dict


def login(data: Dict, conn) -> Response:
    username: str = data.get("username", "")
    password: str = data.get("password", "")

    errors = {}
    if not username:
        errors["username"] = "Username cannot be empty"
    if not password:
        errors["password"] = "Password cannot be empty"

    if errors:
        return Response(False, errors)

    user = db.get_user(username=username)
    if not user:
        errors["message"] = "User not found"
        return Response(False, errors)

    is_password_correct = crypt.check_password(password, user.password)
    if is_password_correct:
        tokens = crypt.create_tokens(user)
        return Response(True, tokens)

    errors["message"] = "Username or Password is invalid"
    return Response(False, errors)


def sign_up(data: Dict, conn) -> Response:
    username: str = data.get("username", "")
    password: str = data.get("password", "")
    email: str = data.get("email", "")
    full_name: str = data.get("full_name", "")

    print("checking")

    errors = {}
    if not username:
        errors["username"] = "Username cannot be empty"
    if not password:
        errors["password"] = "Password cannot be empty"
    if not email:
        errors["email"] = "Email cannot be empty"

    if errors:
        print("errors found")
        return Response(False, errors)

    print("checking user exists")
    user_exists = db.check_user_exists(username=username, email=email)
    if user_exists["username"]:
        errors["username"] = "User with this username already exists."
    if user_exists["email"]:
        errors["email"] = "User with this email already exists."
    if errors:
        print("user found sending erross")
        return Response(False, errors)

    print("crating user")
    user = db.User(**data)
    user.password = crypt.hash_password(user.password)
    user = db.create_user(user)

    tokens = crypt.create_tokens(user)
    return Response(True, tokens)


def authenticate(data: Dict, conn: Connection) -> Response:
    access_token = data.get("access_token", "")

    payload = crypt.validate_access_token(access_token)
    if not payload:
        return Response(False, {"message": "Access token is no valid"})

    user_id = payload.get("sub")
    print("user id: ", user_id)
    user = db.get_user(id=user_id)
    if not user:
        return Response(False, {"message": "User not found"})

    conn.authenticate(user)
    print("user", conn.user)
    return Response(True, {"message": "authenticated"})


@protected
def search_users(data, conn) -> Response:
    query = data.get("q")
    users = db.search_users(query)
    serialized_users = [user.to_dict() for user in users]
    return Response(True, {"results": serialized_users})


def refresh_access_token(data, conn) -> Response:
    refresh_token = data.get("refresh_token")
    access_token = crypt.refresh_access_token(refresh_token)
    if not access_token:
        return Response(False, {"message": "Refresh token is invalid"})

    return Response(True, {"access_token": access_token})


ACTIONS: Dict[str, Callable] = {
    "login": login,
    "sign_up": sign_up,
    "authenticate": authenticate,
    "search_users": search_users,
    "refresh_access_token": refresh_access_token,
}
