from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from bson.objectid import ObjectId
from pymongo import MongoClient

client = MongoClient()
db = client.chat


@dataclass
class User:
    username: str
    email: str
    password: str
    _id: Optional[ObjectId] = None
    avatar: Optional[str] = None
    full_name: Optional[str] = None

    def __repr__(self) -> str:
        return f"<{self._id} - {self.username}>"

    def serialize(self) -> Dict:
        return {
            "username": self.username,
            "display_name": self.full_name if self.full_name else self.username,
            "email": self.email,
            "id": str(self._id),
            "full_name": self.full_name,
            "avatar": self.avatar
        }


@dataclass
class Chat:
    user1: str
    user2: str
    _id: Optional[ObjectId] = None
    last_message: Optional[str] = None
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = field(default_factory=datetime.now)

    def __repr__(self) -> str:
        return f"<{self._id} - {self.user1} - {self.user2}>"

    def serialize(self, user: User):
        if str(self.user1) == str(user._id):
            other_user_id = self.user2
        else:
            other_user_id = self.user1
        other_user = UserManager().get(id=other_user_id)
        other_user = other_user.serialize() if other_user else user.serialize()

        updated_at = self.updated_at.timestamp() if self.updated_at else ""
        return {
            "id": str(self._id),
            "user": other_user,
            "last_message": self.last_message,
            "updated_at": updated_at
        }


@dataclass
class Message:
    class Status(Enum):
        SENDING = "sending"
        SENT = "sent"
        FAILED = "failed"
        READ = "read"

    chat: str
    text: str
    sender: str
    time: Optional[datetime] = field(default_factory=datetime.now)
    _id: Optional[str] = None
    status: Status = Status.SENT

    reply_to: Optional[str] = None

    def serialize(self, user=None):
        if user:
            return {
                "id": str(self._id),
                "text": self.text,
                "is_mine": str(self.sender) == str(user._id),
                "time": self.time.timestamp() if self.time else None,
                "status": self.status.value if type(self.status) != str else self.status,
            }
        return {
            "id": str(self._id),
            "text": self.text,
            "sender": self.sender,
            "time": self.time.timestamp() if self.time else None,
            "status": self.status.value if type(self.status) != str else self.status,
        }


class UserManager:
    def __init__(self) -> None:
        pass

    def get(
        self, id: Optional[str] = None, username: Optional[str] = None, email: Optional[str] = None
    ) -> Optional[User]:
        query = {}
        if id:
            object_id = ObjectId(id)
            query["_id"] = object_id
        if username:
            query["username"] = username
        if email:
            query["email"] = email
        item = db.users.find_one(query)
        if item:
            return User(**item)
        return None

    def check_exists(self, username: Optional[str] = None, email: Optional[str] = None) -> Dict[str, bool]:
        username_exists = db.users.find_one({"username": username}) is not None if username else False
        email_exists = db.users.find_one({"email": email}) is not None if email else False

        return {"username": username_exists, "email": email_exists}

    def create(self, user: User) -> User:
        data = asdict(user)
        data.pop("_id")  # let mongodb assign random id
        item = db.users.insert_one(data)
        user._id = item.inserted_id
        return user

    def update(self, user_id, user: User) -> User:
        user_id = ObjectId(user_id) if type(user_id) is str else user_id
        data = asdict(user)
        data.pop("_id")
        db.users.update_one({"_id": user_id}, {"$set": data})
        user._id = user_id
        return user

    def search(self, q: str) -> List[User]:
        users = db.users.find({"username": {"$regex": q, "$options": "i"}}).limit(10)
        users = [User(**user) for user in users]

        return users


class ChatManager:
    def __init__(self) -> None:
        pass

    def get(self, id: str) -> Optional[Chat]:
        chat = db.chats.find_one({"_id": ObjectId(id)})
        return Chat(**chat) if chat else None

    def get_user_chats(self, user_id: str) -> List[Chat]:
        chats = db.chats.find({"$or": [{"user1": str(user_id)}, {"user2": str(user_id)}]}).sort("updated_at", -1)
        chats = [Chat(**chat) for chat in chats]
        return chats

    def create(self, chat: Chat):
        data = asdict(chat)
        data.pop("_id")
        data["user1"] = str(data["user1"])
        data["user2"] = str(data["user2"])
        item = db.chats.insert_one(data)
        chat._id = item.inserted_id
        return chat

    def check_exists(self, user1: str, user2: str) -> Optional[Chat]:
        item = db.chats.find_one({"$or": [{"user1": str(user1), "user2": str(user2)}, {"user2": str(user1), "user1": str(user2)}]})
        if not item:
            return None
        return Chat(**item)


class MessageManager:
    def __init__(self) -> None:
        pass

    def create(self, message: Message):
        data = {
            "chat": message.chat,
            "text": message.text,
            "sender": str(message.sender),
            "status": message.status.value,
        }
        print(data, "created")
        item = db.messages.insert_one(data)
        db.chats.update_one({"_id": ObjectId(message.chat)}, {"$set": {"last_message": message.text, "updated_at": datetime.now()}})
        message._id = item.inserted_id
        return message

    def get_chat_messages(self, chat_id: str) -> List[Message]:
        messages = db.messages.find({"chat": chat_id})
        messages = [Message(**message) for message in messages]
        return messages


users = UserManager()
chats = ChatManager()
messages = MessageManager()
