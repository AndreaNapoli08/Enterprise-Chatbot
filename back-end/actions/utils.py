# actions/utils.py
import bcrypt
import json
from pathlib import Path
import os

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def hash_password(plain_password: str) -> str:
    """Restituisce l'hash della password in formato stringa UTF-8"""
    return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se la password in chiaro corrisponde all'hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, dict) and "users" in data:
            return data["users"]
        return data

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
