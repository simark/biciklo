import os

import pymongo
from pymongo import json_util
import json
from flask import Flask
from flask import request
from flask import render_template
import db
from data import Membre

app = Flask(__name__)

@app.route('/api/membres', methods=['GET'])
def GetMembres():
  membres = db.DBConnection().membres.find()

  ret = list()

  for membre in membres:
    ret.append(membre)

  return json.dumps(ret, default=json_util.default)


@app.route('/api/membres', methods=['POST'])
def PostMembres():
  membre = Membre()

  result = {'status': 'ok', 'errorstr': 'No error.'}
  required_keys = ['prenom', 'nom', 'courriel']
  optional_keys = ['provenance']

  try:
    for key in required_keys:
      value = request.form[key]
      setattr(membre, key, value)

    for key in optional_keys:
      if key in request.form:
        value = request.form[key]
        setattr(membre, key, value)

    membre.numero = ObtenirProchainNumeroDeMembre()

    db.DBConnection().membres.insert(membre.__dict__)

    print "Nouveau membre, numero %d" % membre.numero

  except KeyError as ex:
    result['status'] = 'bad'
    result['errorstr'] = 'Parameter missing: %s.' % ex.message

  return json.dumps(result) + '\n'

@app.route('/membres', methods=['GET'])
def ListeMembres():
  print os.getcwd()
  return render_template('membres.html', var="lol")

def ObtenirProchainNumeroDeMembre():
  """Retourne le prochain numero de membre disponible."""
  d = db.DBConnection()

  if d.membres.count() == 0:
    return 1
  else:
    return db.DBConnection().membres.find().sort('numero', pymongo.DESCENDING).limit(1)[0]['numero'] + 1


if __name__ == '__main__':
  if 'BICIKLO_DEBUG' in os.environ:
    app.debug = True

  app.run()

