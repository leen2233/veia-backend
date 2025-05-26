import os
from dotenv import load_dotenv

load_dotenv()

BIND_HOST = os.getenv("BIND_HOST", "127.0.0.1")
BIND_PORT = int(os.getenv("BIND_PORT", "9090"))
SECRET_KEY = os.getenv("SECRET_KEY")

