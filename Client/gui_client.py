import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
from UserRegistration import authenticate_user
from UserRegistration import register_user
import socket
import json
import threading
import datetime, pytz


class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Application")
        self.username = None
        self.server_address = ('192.168.1.37', 12345)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.login_frame = tk.Frame(root)
        self.chat_frame = tk.Frame(root)
        
        self.create_login_frame()
        
    def create_login_frame(self):
        self.login_frame.pack(pady=10)
        
        tk.Label(self.login_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(self.login_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = tk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Button(self.login_frame, text="Login", command=self.authenticate).grid(row=2, column=0, pady=10)
        tk.Button(self.login_frame, text="Register", command=self.register).grid(row=2, column=1, pady=10)
        
    def authenticate(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        auth_status = authenticate_user(username, password)
        if auth_status == "Authentication successful":
            messagebox.showinfo("Login Success", auth_status)
            self.username = username
            self.login_frame.pack_forget()
            self.create_chat_frame()
            self.load_user_chatrooms()
        else:
            messagebox.showerror("Login Failed", auth_status)
    
    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        registration_status = register_user(username, password)
        if registration_status == "User registered successfully":
            messagebox.showinfo("Register Success", registration_status)
            self.username = username
            self.login_frame.pack_forget()
            self.create_chat_frame()
            self.load_user_chatrooms()
        else:
            messagebox.showerror("Login Failed", registration_status)
    
    def create_chat_frame(self):
        self.chat_frame.pack(fill='both', expand=True)
        
        self.room_list_frame = tk.Frame(self.chat_frame, width=200)
        self.room_list_frame.pack(side='left', fill='y', padx=10, pady=10)
        
        self.chat_display_frame = tk.Frame(self.chat_frame)
        self.chat_display_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)
        
        self.chat_display = scrolledtext.ScrolledText(self.chat_display_frame, width=50, height=20, state='disabled')
        self.chat_display.pack(padx=10, pady=10)
        
        self.message_entry = tk.Entry(self.chat_display_frame, width=40)
        self.message_entry.pack(side='left', padx=10, pady=5)
        
        tk.Button(self.chat_display_frame, text="Send", command=self.send_message).pack(side='left', padx=5, pady=5)
        
        self.add_chatroom_button = tk.Button(self.room_list_frame, text="Add Chatroom", command=self.add_chatroom)
        self.add_chatroom_button.pack(pady=5)
        
        self.room_list = tk.Listbox(self.room_list_frame)
        self.room_list.pack(fill='both', expand=True)
        self.room_list.bind('<<ListboxSelect>>', self.load_chatroom)
        
        self.rooms = {'Global Chatroom': None}  # Store chatroom details here
        self.update_room_list()
        
        self.start_global_listener()
    
    def load_user_chatrooms(self):
        request = {
            "action": "get_user_chatrooms",
            "username": self.username
        }
        self.client_socket.sendto(json.dumps(request).encode(), self.server_address)
        data, _ = self.client_socket.recvfrom(1024)
        response = json.loads(data.decode())
        
        if response["status"] == "success":
            chatrooms = response["chatrooms"]
            for chatroom in chatrooms:
                if chatroom["users"][1] == self.username:
                    self.rooms.update({chatroom["users"][0]: chatroom["_id"]})
                elif chatroom["users"][0] == self.username:
                    self.rooms.update({chatroom["users"][1]: chatroom["_id"]})
            self.update_room_list()
        else:
            messagebox.showerror("Error", response["message"])
        
    def start_global_listener(self):
        listener_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        listener_thread.start()
        
    def listen_for_messages(self):
        while True:
            try:
                data, _ = self.client_socket.recvfrom(1024)
                response = json.loads(data.decode())
                if "message" in response and "sender" in response:
                    timestamp = datetime.datetime.fromisoformat(response['timestamp']).astimezone(pytz.timezone('Europe/Istanbul')) 
                    self.display_message(response['sender'], response['message'], timestamp)
            except Exception as e:
                print(f"Error receiving message: {e}")
    
    def display_message(self, sender, message, timestamp):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{timestamp} - {sender}: {message}\n")
        self.chat_display.config(state='disabled')
        self.chat_display.yview(tk.END)
    
    def send_message(self):
        message = self.message_entry.get()
        if message:
            selected_room = self.room_list.get(tk.ACTIVE)
            if selected_room == 'Global Chatroom':
                send_request = {
                    "action": "send_global_message",
                    "sender": self.username,
                    "message": message
                }
            else:
                send_request = {
                    "action": "send_message",
                    "chatroom_id": self.rooms[selected_room],
                    "sender": self.username,
                    "message": message
                }
            self.client_socket.sendto(json.dumps(send_request).encode(), self.server_address)
            self.message_entry.delete(0, tk.END)
    
    def add_chatroom(self):
        user2 = simpledialog.askstring("Private Chat", "Enter the username of the user you want to chat with:")
        if user2:
            create_request = {
                "action": "create_chatroom",
                "user1": self.username,
                "user2": user2
            }
            self.client_socket.sendto(json.dumps(create_request).encode(), self.server_address)
            data, _ = self.client_socket.recvfrom(1024)
            response = json.loads(data.decode())
            if response["status"] == "success":
                chatroom_id = response["chatroom_id"]
                self.rooms[user2] = chatroom_id
                self.update_room_list()
            else:
                messagebox.showerror("Error", response["message"])
    
    def load_chatroom(self, event):
        selected_room = self.room_list.get(self.room_list.curselection())
        if selected_room != 'Global Chatroom':
            get_messages_request = {
                "action": "get_messages",
                "chatroom_id": self.rooms[selected_room]
            }
            self.client_socket.sendto(json.dumps(get_messages_request).encode(), self.server_address)
            data, _ = self.client_socket.recvfrom(1024)
            response = json.loads(data.decode())
            if response["status"] == "success" and "messages" in response:
                messages = response["messages"]
                self.chat_display.config(state='normal')
                self.chat_display.delete('1.0', tk.END)
                for msg in messages:
                    self.chat_display.insert(tk.END, f"{msg['timestamp']} - {msg['sender']}: {msg['message']}\n")
                self.chat_display.config(state='disabled')
                self.chat_display.yview(tk.END)
        else:
            self.chat_display.config(state='normal')
            self.chat_display.delete('1.0', tk.END)
    
    def update_room_list(self):
        self.room_list.delete(0, tk.END)
        for room in self.rooms.keys():
            self.room_list.insert(tk.END, room)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
