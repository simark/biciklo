import pymongo

class DBConnection():
  def __init__(self, dbname='biciklo'):
    self.connection = pymongo.Connection()
    self.db = self.connection[dbname]
    self.membres = self.db.membres
