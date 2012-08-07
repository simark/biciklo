from datetime import datetime
import json
import os

import pymongo
from bson import json_util

from flask import Flask
from flask import request
from flask import render_template

from data import Membre
import db

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
  def ValiderValeur(choix_valeurs, cle, valeur):
    if cle in choix_valeurs:
      if not valeur in choix_valeurs[cle]:
        raise ValueError(cle)

  membre = Membre()

  result = {'status': 'ok', 'errorstr': 'No error.'}
  required_keys = ['prenom', 'nom', 'courriel', 'type']
  optional_keys = ['provenance']

  choix_valeurs = {
    'type': ['permanent', 'annuel', 'mensuel'],
  }

  try:
    for key in required_keys:
      value = request.form[key]
      ValiderValeur(choix_valeurs, key, value)
      setattr(membre, key, value)

    for key in optional_keys:
      if key in request.form:
        value = request.form[key]
        ValiderValeur(choix_valeurs, key, value)
        setattr(membre, key, value)


    membre.numero = ObtenirProchainNumeroDeMembre()
    membre.date_apparition = datetime.now()
    # TODO: check if mensuel or annuel, setter la date d'echeance
    # Setter la date "first time seen"
    # Setter la date de l'abonnement courant (now)

    db.DBConnection().membres.insert(membre.__dict__)

    print datetime.now

    print "Nouveau membre, numero %d" % membre.numero

  except KeyError as ex:
    result['status'] = 'bad'
    result['errorstr'] = 'Parametre manquant: "%s".' % ex.message
  except ValueError as ex:
    result['status'] = 'bad'
    result['errorstr'] = 'Valeur invalide pour "%s".' % ex.message

  return json.dumps(result) + '\n'

@app.route('/membres', methods=['GET'])
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

