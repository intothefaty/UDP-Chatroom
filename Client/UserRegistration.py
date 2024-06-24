from DBConnection import db
import hashlib


Chat = db["Chatroom"]
Users = db["Users"]

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    hashed_password = hash_password(password)
    user = {
        "username": username,
        "password": hashed_password
    }
    if Users.find_one({"username": username}):
        return "Username already exists"
    Users.insert_one(user)
    return "User registered successfully"

def authenticate_user(username, password):
    hashed_password = hash_password(password)
    user = Users.find_one({"username": username, "password": hashed_password})
    if user:
        return "Authentication successful"
    else:
        return "Invalid username or password"
