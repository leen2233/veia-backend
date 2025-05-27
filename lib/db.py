from dataclasses import asdict, dataclass
from typing import Dict, Optional

from pymongo import MongoClient

client = MongoClient()
db = client.chat


@dataclass
class User:
    username: str
    email: str
    password: str
    _id: Optional[str] = None
    full_name: Optional[str] = None

    def __repr__(self) -> str:
        return f"<{self._id} - {self.username}>"


def get_user_by_username(username) -> Optional[User]:
    item = db.users.find_one({"username": username})
    if item:
        return User(**item)
    return None


def check_user_exists(username: Optional[str] = None, email: Optional[str] = None) -> Dict[str, bool]:
    username_exists = db.users.find_one({"username": username}) is not None
    email_exists = db.users.find_one({"username": username}) is not None

    return {"username": username_exists, "email": email_exists}


def create_user(user: User):
    data = asdict(user)
    data.pop("_id")  # let mongodb assign random id
    item = db.users.insert_one(data)
    user._id = item.inserted_id
    print(user)
    return user
