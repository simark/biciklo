from pymongo import MongoClient

class DBConnection():
  def __init__(self, dbname='biciklo'):
    self.client = MongoClient()
    self.db = self.client[dbname]
    self.membres = self.db.membres
    self.pieces = self.db.pieces

