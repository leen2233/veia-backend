from dataclasses import asdict, dataclass
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
    full_name: Optional[str] = None

    def __repr__(self) -> str:
        return f"<{self._id} - {self.username}>"

    def to_dict(self) -> Dict:
        return {"username": self.username, "email": self.email, "id": str(self._id), "full_name": self.full_name}


def get_user(id: Optional[str] = None, username: Optional[str] = None, email: Optional[str] = None) -> Optional[User]:
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


def check_user_exists(username: Optional[str] = None, email: Optional[str] = None) -> Dict[str, bool]:
    username_exists = db.users.find_one({"username": username}) is not None
    email_exists = db.users.find_one({"username": username}) is not None

    return {"username": username_exists, "email": email_exists}


def create_user(user: User) -> User:
    data = asdict(user)
    data.pop("_id")  # let mongodb assign random id
    item = db.users.insert_one(data)
    user._id = item.inserted_id
    print(user)
    return user


def search_users(q: str) -> List[User]:
    users = db.users.find({"username": {"$regex": q, "$options": "i"}}).limit(10)
    users = [User(**user) for user in users]

    return users
