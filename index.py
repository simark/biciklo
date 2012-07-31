import os
import pymongo
import json

import db

from flask import Flask
from flask import request

from data import Membre

app = Flask(__name__)

@app.route('/membres', methods=['GET'])
def GetMembres():
  return 'Hello Get!'

@app.route('/membres', methods=['POST'])
def PostMembres():
  membre = Membre()
  
  result = {'status': 'ok', 'errorstr': 'No error.'}
  
  try:
    membre.prenom = request.form['prenom']
    membre.nom = request.form['nom']
    membre.courriel = request.form['courriel']
    
    d = db.DBConnection()
    print d.membres.insert(membre.__dict__)
  except KeyError as ex:
    result['status'] = 'bad'
    result['errorstr'] = 'Parameter missing: %s.' % ex.message

  return json.dumps(result) + '\n'

if __name__ == '__main__':
  if 'BICIKLO_DEBUG' in os.environ:
	app.debug = True
  app.run()

