from datetime import datetime
import json
import os
import time

import pymongo
from bson import json_util

from flask import Flask
from flask import request
from flask import render_template

import db

app = Flask(__name__)

# Cles requises pour un membre
required_keys = ['prenom', 'nom', 'courriel', 'listedenvoi', 'provenance']

# Cles optionnelles pour un membre
optional_keys = []

# Map key to list of valid choices.
choix_valeurs = {
  'listedenvoi': ['non', 'oui', 'fait'],
}

@app.route('/api/membres', methods=['GET'])
def GetMembres():
  membres = db.DBConnection().membres.find()

  ret = list()

  for membre in membres:
    ret.append(membre)

  return json.dumps(ret, default=json_util.default)


@app.route('/api/membres', methods=['POST'])
def PostMembres():
  def ValiderValeur(choix_valeurs, cle, valeur):
    if cle in choix_valeurs:
      if not valeur in choix_valeurs[cle]:
        raise ValueError(cle)

  membre = {}

  result = {'status': 'ok', 'errorstr': 'No error.'}

  try:
    for key in required_keys:
      value = request.form[key]
      ValiderValeur(choix_valeurs, key, value)
      membre[key] = value

    for key in optional_keys:
      if key in request.form:
        value = request.form[key]
        ValiderValeur(choix_valeurs, key, value)
        membre[key] = value

    membre['numero'] = ObtenirProchainNumeroDeMembre()
    membre['dateinscription'] = datetime.now()

    db.DBConnection().membres.insert(membre)

    result['numero'] = membre['numero']
  except KeyError as ex:
    result['status'] = 'bad'
    result['errorstr'] = 'Parametre manquant: "%s".' % ex.message
  except ValueError as ex:
    result['status'] = 'bad'
    result['errorstr'] = 'Valeur invalide pour "%s".' % ex.message

  return json.dumps(result) + '\n'

@app.route('/api/membres/<int:numero>', methods=['PUT'])
def ModifierMembre(numero):
  result = {'status': 'ok', 'errorstr': 'No error.'}

  try:
    valeurs = {}

    for key in request.form:
      valeur = request.form[key]
      if key in required_keys or key in optional_keys:
        if key in choix_valeurs:
          if valeur not in choix_valeurs[key]:
            raise ValueError(key)

        valeurs[key] = valeur

    request_result = db.DBConnection().membres.update(
        {'numero': numero},
        {'$set': valeurs},
        safe=True)

    if not request_result['updatedExisting']:
      result['status'] = 'bad'
      result['errorstr'] = 'Aucune entree trouvee pour numero %s' % numero

  except ValueError as ex:
    result['status'] = 'bad'
    result['errorstr'] = 'Valeur invalide pour "%s"' % ex.message

  return json.dumps(result) + '\n'

@app.route('/api/prenoms', methods=['GET'])
def ListePrenoms():
  liste = db.DBConnection().membres.find(fields = ['prenom'])

  term = ''
  if 'term' in request.args:
    term = request.args['term'].lower()

  prenoms = set()
  for item in liste:
    prenom = item['prenom']
    if prenom.lower().startswith(term):
      prenoms.add(item['prenom'])

  prenoms = sorted(prenoms)
  return json.dumps(prenoms) + '\n'

@app.route('/membres/', methods=['GET'])
def ListeMembres():
  print os.getcwd()
  return render_template('membres.html')

@app.route('/membres/<int:numero>', methods=['GET'])
def UnMembre(numero):
  membre =  db.DBConnection().membres.find_one({'numero': numero})
  return render_template('membre.html', numero=numero, membre=membre)

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

  app.run(host='0.0.0.0')

