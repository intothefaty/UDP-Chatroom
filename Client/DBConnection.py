import pymongo

url = "mongodb+srv://barandatlar:12345@cluster0.vmhvo8u.mongodb.net/"
client = pymongo.MongoClient(url)

db = client["UDPChatroom"]