import pymongo

global_dbcon = None

def DBConnection():
	global global_dbcon

	if not global_dbcon:
		global_dbcon = DBConnectionClass()

	return global_dbcon

class DBConnectionClass():
  def __init__(self, dbname='biciklo'):
    self.client = pymongo.MongoClient()
    self.db = self.client[dbname]
    self.membres = self.db.membres
    self.pieces = self.db.pieces
    self.factures = self.db.factures
