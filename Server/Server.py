import socket
import json
from bson.objectid import ObjectId
from PrivateChatroom import *

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

def start_server():
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('0.0.0.0', 12345)) 
    print("Server started and listening on port 12345")

    clients = set()

    while True:
        data, address = server_socket.recvfrom(1024)
        if address not in clients:
            clients.add(address)
            print(f"New client connected from {address}")

        print(f"Received message from {address}: {data.decode()}")
        handle_message(data, address, clients)

def handle_message(data, address, clients):
    try:
        message = json.loads(data)
        action = message.get("action")

        print(f"Action: {action}")

        if action == "create_chatroom":
            user1 = message.get("user1")
            user2 = message.get("user2")
            chatroom_id = create_chatroom(user1, user2)
            response = {"status": "success", "chatroom_id": str(chatroom_id)} if not str(chatroom_id).startswith("Error") else {"status": "error", "message": chatroom_id}
            server_socket.sendto(json.dumps(response).encode(), address)

        elif action == "send_message":
            chatroom_id = ObjectId(message.get("chatroom_id"))
            sender = message.get("sender")
            chat_message = message.get("message")
            send_message(chatroom_id, sender, chat_message)
            response = {
                "status": "success",
                "message": chat_message,
                "sender": sender,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Tüm istemcilere mesajı yayınla
            for client in clients:
                server_socket.sendto(json.dumps(response).encode(), client)
                
        elif action == "get_messages":
            chatroom_id = ObjectId(message.get("chatroom_id"))
            messages = get_chatroom_messages(chatroom_id)
            response = {"status": "success", "messages": messages}
            server_socket.sendto(json.dumps(response, cls=DateTimeEncoder).encode(), address)

        elif action == "get_user_chatrooms":
            username = message.get("username")
            chatrooms = get_chatrooms(username)
            response = {"status": "success", "chatrooms": chatrooms}
            server_socket.sendto(json.dumps(response, cls=DateTimeEncoder).encode(), address)

        elif action == "send_global_message":
            sender = message.get("sender")
            chat_message = message.get("message")
            response = {
                "status": "success",
                "message": chat_message,
                "sender": sender,
                "timestamp": datetime.datetime.now().isoformat()
            }

            # Tüm istemcilere global mesajı yayınla
            for client in clients:
                server_socket.sendto(json.dumps(response).encode(), client)

    except Exception as e:
        print(f"Error: {e}")
        response = {"status": "error", "message": str(e)}
        server_socket.sendto(json.dumps(response).encode(), address)





if __name__ == "__main__":
    start_server()
