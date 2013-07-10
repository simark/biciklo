from pymongo import Connection

class DBConnection():
  def __init__(self, dbname='biciklo'):
    self.client = Connection()
    self.db = self.client[dbname]
    self.membres = self.db.membres
    self.pieces = self.db.pieces
