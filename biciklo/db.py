import pymongo

class DBConnection():
  def __init__(self, dbname='biciklo'):
    self.client = pymongo.MongoClient()
    self.db = self.client[dbname]
    self.membres = self.db.membres
    self.pieces = self.db.pieces
    self.factures = self.db.factures
