from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.results import UpdateResult

from utils.server_holder import handle_update

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
    last_seen: Optional[datetime] = field(default_factory=datetime.now)

    def __repr__(self) -> str:
        return f"<{self._id} - {self.username}>"

    def serialize(self) -> Dict:
        return {
            "username": self.username,
            "display_name": self.full_name if self.full_name else self.username,
            "email": self.email,
            "id": str(self._id),
            "full_name": self.full_name,
            "avatar": self.avatar,
            "last_seen": self.last_seen.timestamp() if self.last_seen else None
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

    def serialize(self, user: User, serialize_user=True):
        if str(self.user1) == str(user._id):
            other_user_id = self.user2
        else:
            other_user_id = self.user1
        if serialize_user:
            other_user = UserManager().get(id=other_user_id)
            other_user = other_user.serialize() if other_user else user.serialize()
        else:
            other_user = other_user_id

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
        SENT = "sent"
        READ = "read"

    chat: str
    text: str
    sender: str
    time: Optional[datetime] = field(default_factory=datetime.now)
    _id: Optional[str] = None
    status: Status = Status.SENT

    reply_to: Optional[str] = None

    def serialize(self, user=None):
        if self.reply_to:
            reply_to = MessageManager().get(id=self.reply_to)
            if reply_to:
                reply_to = reply_to.serialize(user=user)
            else:
                reply_to = None
        else:
            reply_to = None
        data = {
            "id": str(self._id),
            "text": self.text,
            "time": self.time.timestamp() if self.time else None,
            "status": self.status.value if type(self.status) is not str else self.status,
            "reply_to": reply_to,
            "chat_id": str(self.chat)
        }
        if user:
            data["is_mine"] = str(self.sender) == str(user._id)
        else:
            data["sender"] = str(self.sender)
        return data

    def to_dict(self):
        return {
            "chat": self.chat,
            "text": self.text,
            "sender": str(self.sender),
            "status": self.status.value,
            "time": self.time,
            "reply_to": self.reply_to
        }

@dataclass
class Update:
    type: str
    body: dict
    users: List[str]
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    _id: Optional[str] = None

    def to_dict(self):
        return {
            "type": self.type,
            "body": self.body,
            "created_at": self.created_at.timestamp() if self.created_at else None,
            "id": str(self._id)
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

    def get(self, id: str) -> Optional[Message]:
        chat = db.messages.find_one({"_id": ObjectId(id)})
        return Message(**chat) if chat else None

    def create(self, message: Message):
        data = message.to_dict()
        item = db.messages.insert_one(data)
        db.chats.update_one({"_id": ObjectId(message.chat)}, {"$set": {"last_message": message.text, "updated_at": datetime.now()}})
        message._id = item.inserted_id
        return message

    def update(self, message_id: str, data: dict):
        result: UpdateResult = db.messages.update_one({"_id": ObjectId(message_id)}, {"$set": data})
        return result.modified_count > 0

    def update_many(self, message_ids: List[str], data: dict, chat_id: Optional[str] = None,):
        object_ids = [ObjectId(mid) for mid in message_ids]
        query: dict = {"_id": {"$in": object_ids}}
        if chat_id:
            query["chat"] = chat_id
        result: UpdateResult = db.messages.update_many(query, {"$set": data})
        return result.modified_count > 0

    def delete(self, message_id: str) -> bool:
        id = ObjectId(message_id)
        db.messages.delete_one({"_id": id})
        return True

    def get_chat_messages(self, chat_id: str, limit: int = 10, last_message: Optional[str] = None) -> Tuple[List[Message], bool]:
        query: dict = {"chat": chat_id}
        if last_message:
            query["_id"] = {"$lt": ObjectId(last_message)}
        messages = db.messages.find(query).sort('time', -1).limit(limit)

        messages = [Message(**message) for message in messages]
        messages.reverse()

        # know if has earlier message
        first_message = messages[0]
        has_earlier_message = db.messages.count_documents({"time": {"$lt": first_message.time}, "chat": first_message.chat}) > 0

        return messages, has_earlier_message


class UpdateManager:
    def __init__(self) -> None:
        pass

    def get(self, user: str, created_at: Optional[datetime]=None) -> List[Update]:
        query: dict = {"users": user}
        if created_at:
            query["created_at"] = {"$gt": created_at}

        updates = db.updates.find(query)
        updates = [Update(**update) for update in updates]
        return updates

    def create(self, update: Update) -> Update:
        data = asdict(update)
        data.pop("_id")
        item = db.updates.insert_one(data)
        update._id = item.inserted_id

        handle_update(update)

        return update


users = UserManager()
chats = ChatManager()
messages = MessageManager()
updates = UpdateManager()
