from dataclasses import dataclass
from typing import Dict, Optional

from lib import db
from lib.connection import Connection
from utils import crypt
from utils.decorators import protected


@dataclass
class Response:
    status: bool
    data: Dict
    additional_data: Optional[Dict] = None
    send_now: bool = True


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

    user = db.users.get(username=username)
    if not user:
        errors["message"] = "Username or Password is invalid"
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

    errors = {}
    if not username:
        errors["username"] = "Username cannot be empty"
    if not password:
        errors["password"] = "Password cannot be empty"
    if not email:
        errors["email"] = "Email cannot be empty"

    if errors:
        return Response(False, errors)

    user_exists = db.users.check_exists(username=username, email=email)
    if user_exists["username"]:
        errors["username"] = "User with this username already exists."
    if user_exists["email"]:
        errors["email"] = "User with this email already exists."
    if errors:
        return Response(False, errors)

    user = db.User(**data)
    user.password = crypt.hash_password(user.password)
    user = db.users.create(user)

    tokens = crypt.create_tokens(user)
    return Response(True, tokens)


def authenticate(data: Dict, conn: Connection) -> Response:
    access_token = data.get("access_token", "")

    payload = crypt.validate_access_token(access_token)
    if not payload:
        return Response(False, {"message": "Access token is no valid"})

    user_id = payload.get("sub")
    user = db.users.get(id=user_id)
    if not user:
        return Response(False, {"message": "User not found"})

    conn.authenticate(user)
    return Response(True, {"message": "authenticated", "user": user.serialize()})

@protected
def update_user(data, conn) -> Response:
    user = conn.user

    username = data.get("username")
    if username != user.username and db.users.check_exists(username=username).get("username"):
        return Response(False, {"username": "User with this username already exists"})

    updated_user = db.User(
        username=username,
        email=user.email,
        password=user.password,
        avatar=data.get("avatar", user.avatar),
        full_name=data.get("full_name", user.full_name)
    )
    updated_user = db.users.update(user._id, updated_user)
    conn.authenticate(updated_user)

    return Response(True, {"user": updated_user.serialize()})


@protected
def search_users(data, conn) -> Response:
    query = data.get("q")
    users = db.users.search(query)
    serialized_users = [user.serialize() for user in users]
    return Response(True, {"results": serialized_users})


def refresh_access_token(data, conn) -> Response:
    refresh_token = data.get("refresh_token")
    access_token = crypt.refresh_access_token(refresh_token)
    if not access_token:
        return Response(False, {"message": "Refresh token is invalid"})

    return Response(True, {"access_token": access_token})


@protected
def get_chats(data, conn) -> Response:
    user = conn.user
    chats = db.chats.get_user_chats(user._id)
    chats_serialized = [chat.serialize(user) for chat in chats]
    return Response(True, {"results": chats_serialized})


@protected
def new_message(data, conn) -> Response:
    chat_id = data.get("chat_id", "")
    chat = None
    if not chat_id:
        user_id = data.get("user_id")
        chat = db.chats.check_exists(conn.user._id, user_id)
        if not chat:
            if not user_id:
                return Response(False, {"message": "chat id or user id required"})
            chat = db.Chat(user1=conn.user._id, user2=user_id)
            chat = db.chats.create(chat)
        chat_id = str(chat._id)
    else:
        chat = db.chats.get(chat_id)

    text = data.get("text")
    reply_to = data.get("reply_to")
    message = db.Message(text=text, sender=conn.user._id, chat=chat_id, reply_to=reply_to)
    message = db.messages.create(message)

    message_serialized = message.serialize()
    chat_serialized = chat.serialize(conn.user) if chat else None

    data = {"message": message_serialized, "chat": chat_serialized}

    if chat:
        update = db.Update(type="new_message", body=data, users=list(set([chat.user1, chat.user2])))
        db.updates.create(update)

    return Response(True, {}, send_now=False)


@protected
def get_messages(data, conn) -> Response:
    chat = None
    chat_id = data.get("chat_id", "")
    last_message = data.get("last_message")
    
    if not chat_id:
        user_id = data.get("user_id")
        chat = db.chats.check_exists(conn.user._id, user_id)
        if not chat:
            if not user_id:
                return Response(False, {"message": "chat id or user id required"})
            chat = db.Chat(user1=conn.user._id, user2=user_id)
            chat = db.chats.create(chat)
        chat_id = str(chat._id)

    if not chat:
        chat = db.chats.get(chat_id)
        if not chat:
            return Response(False, {"message": "chat not found"})

    messages, has_more = db.messages.get_chat_messages(chat_id, limit=20, last_message=last_message)
    messages_serialized = [message.serialize() for message in messages]
    return Response(True, {"results": messages_serialized, "chat": chat.serialize(conn.user), "has_more": has_more})


@protected
def delete_message(data, conn: Connection) -> Response:
    message_id = data.get("message_id")
    message = db.messages.get(message_id)
    if not message:
        return Response(False, {"message": "message not found"})

    if not conn.user or message.sender != str(conn.user._id):
        return Response(False, {"message": "permission error"})

    chat = db.chats.get(id=message.chat)

    db.messages.delete(message_id)
    if chat:
        update = db.Update(type="delete_message", body={"message_id": message_id}, users=list(set([chat.user1, chat.user2])))
        db.updates.create(update)

    return Response(True, {}, send_now=False)


@protected
def edit_message(data, conn: Connection) -> Response:
    message_id = data.get("message_id")
    text = data.get("text")
    message = db.messages.get(message_id)
    if not message:
        return Response(False, {"message": "message not found"})

    if not conn.user or message.sender != str(conn.user._id):
        return Response(False, {"message": "permission error"})

    chat = db.chats.get(id=message.chat)
    db.messages.update(message_id, {"text": text})

    if chat:
        update = db.Update(type="edit_message", body={"message_id": message_id, "text": text}, users=list(set([chat.user1, chat.user2])))
        db.updates.create(update)

    return Response(True, {}, send_now=False)


@protected
def read_message(data, conn: Connection) -> Response:
    message_id = data.get("message_id")
    message_ids = data.get("message_ids", []) # for multiple

    updated = False
    if message_id:
        message_ids.append(message_id)
    updated = db.messages.update_many(message_ids, {"status": db.Message.Status.READ.value})

    users_to_notify = set()
    chats = set()

    if updated:
        for id in message_ids:
            message = db.messages.get(id)
            if message and message.chat not in chats:
                chat = db.chats.get(message.chat)
                chats.add(message.chat)
                if chat:
                    user_to_notify = ""
                    if conn.user and str(chat.user1) == str(conn.user._id):
                        user_to_notify = chat.user2
                    elif conn.user and str(chat.user2) == str(conn.user._id):
                        user_to_notify = chat.user1
                    users_to_notify.add(str(user_to_notify))

    data = {"ids": message_ids, "status": "read"}
    update = db.Update(type="read_message", body=data, users=list(users_to_notify))
    db.updates.create(update)

    return Response(updated, {}, send_now=False)
