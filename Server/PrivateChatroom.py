import datetime
from bson.objectid import ObjectId
from UserRegistration import Chat, Users

def create_chatroom(user1, user2):
    if not Users.find_one({"username": user2}):
        return "Error: User2 does not exist"
    
    existing_chatroom = Chat.find_one({"users": {"$all": [user1, user2]}})
    if existing_chatroom:
        return existing_chatroom['_id']

    chatroom = {
        "users": [user1, user2],
        "messages": []
    }
    result = Chat.insert_one(chatroom)
    return result.inserted_id

def send_message(chatroom_id, sender, message):
    message_data = {
        "sender": sender,
        "message": message,
        "timestamp": datetime.datetime.now().isoformat()
    }
    Chat.update_one(
        {"_id": ObjectId(chatroom_id)},
        {"$push": {"messages": message_data}}
    )

def get_chatroom_messages(chatroom_id):
    chatroom = Chat.find_one({"_id": ObjectId(chatroom_id)})
    return chatroom['messages'] if chatroom else []

def get_chatrooms(username):
    chatrooms = Chat.find({"users": username})
    return [{"_id": str(chat["_id"]), "users": chat["users"]} for chat in chatrooms]
