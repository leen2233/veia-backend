from dataclasses import asdict, dataclass
from typing import Dict, Optional
from pymongo import MongoClient

client = MongoClient()
db = client.chat

@dataclass
class User:
    username: str
    full_name: str
    email: str
    password: str


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
    item = db.users.insert_one(asdict(user))
    return user
    
