from pymongo import MongoClient

uri = "mongodb+srv://hoangtrungkien4:R22QsguGNpBfTHlw@billreader.kc3jt.mongodb.net/?retryWrites=true&w=majority&appName=BillReader"
client = MongoClient(uri)

db = client['my_database']
accounts = db['account']
users = db['user']
bills = db['bill']