# ---------------------------------------------------
# Version: 01.10.2024
# Author: M. Weber
# ---------------------------------------------------
# 09.06.2024 Bug fixes. Implemented Vorname and Nachname.
# 16.06.2024 check_user() returns user object or empty string.
# 01.10.2024 Added tracking of user actions.
# 01.10.2024 Decrypted user_password in database.
# ---------------------------------------------------

from datetime import datetime
import os
import hashlib
from dotenv import load_dotenv

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# Define constants ----------------------------------
load_dotenv()

mongoClient = MongoClient(os.environ.get('MONGO_URI_DVV'))
database = mongoClient.user_pool
collection_user_pool = database.users
collection_tracking = database.tracking

# User Hash Functions -----------------------------------------

def hash_string(string: str) -> str:
    """Generates a SHA-256 hash for the given string."""
    return hashlib.sha256(string.encode('utf-8')).hexdigest()

def add_user_hash(user_name, user_pw) -> bool:
    try:
        collection_user_pool.insert_one({
            'username': user_name,
            'user_password': hash_string(user_pw),
            'created': datetime.now()
        })
        return True
    except DuplicateKeyError:
        return False
    
def check_user_hash(user_name, user_pw) -> str:
    user = collection_user_pool.find_one({
        'username': user_name,
        'user_password': hash_string(user_pw)
    })
    return user if user else ""

def update_user_hash(user_name: str, new_user_pw: str) -> bool:
    collection_user_pool.update_one(
        {'username': user_name},
        {'$set': {'user_password': hash_string(new_user_pw)}}
    )
    return True

# User Functions -----------------------------------------

def add_user(user_name, user_pw) -> bool:
    try:
        collection_user_pool.insert_one({
            'username': user_name,
            'user_password': user_pw,
            'created': datetime.now()
        })
        return True
    except DuplicateKeyError:
        return False  

def check_user(user_name, user_pw) -> str:
    user = collection_user_pool.find_one({
        'username': user_name,
        'user_password': user_pw
    })
    return user if user else ""

def delete_user(user_name) -> bool:
    collection_user_pool.delete_one({'username': user_name})
    return True

def list_users() -> list:
    users = collection_user_pool.find()
    return users

# Tracking Functions -----------------------------------------

def save_action(user_name: str, action_type: str = "", action: str = "") -> bool:
    collection_tracking.insert_one({
        'username': user_name,
        'action_type': action_type,
        'action': action,
        'created': datetime.now()
    })
    return True