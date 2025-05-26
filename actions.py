from typing import Callable, Dict, Tuple
from lib import db
from utils.crypt import check_password, create_tokens
from dataclasses import dataclass

@dataclass
class Response:
    status: bool
    data: Dict


def login(data: Dict) -> Response:
    username: str = data.get("username", "")
    password: str = data.get("password", "")

    errors = {}
    if not username:
        errors["username"] = "Username cannot be empty"
    if not password:
        errors["password"] = "Password cannot be empty"

    if errors:
        return Response(False, errors)

    user = db.get_user_by_username(username)
    if not user:
        errors["message"] = "User not found"
        return Response(False, errors)

    is_password_correct = check_password(password, user.password)
    if is_password_correct:
        tokens = create_tokens(user)
        return Response(True, tokens)

    errors["message"]= "Username or Password is invalid"
    return Response(False, errors)


def sign_up(data: Dict) -> Response:
    username: str = data.get("username", "")
    password: str = data.get("password", "")
    email: str = data.get("email", "")
    full_name: str = data.get("full_name", "")

    errors = {}
    if not username:
        errors["username"] = "Username cannot be empty"
    if not password:
        errors["password"] = "Password cannot be empty"
    if not email:
        errors["email"] = "Email cannot be empty"

    if errors:
        return Response(False, errors)

    user_exists = db.check_user_exists(username=username, email=email)
    if user_exists["username"]:
        errors["username"] = "User with this username already exists."
    if user_exists["email"]:
        errors["email"] = "User with this email already exists."
    if errors:
        return Response(False, errors)

    user = db.User(**data)
    user = db.create_user(user)

    tokens = create_tokens(user)
    return Response(True, tokens)

ACTIONS: Dict[str, Callable] = {
    "login": login,
    "sign_up": sign_up
}
