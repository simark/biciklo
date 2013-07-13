# -*- coding: utf-8 -*-
from datetime import datetime
import json
import os
import time
import httplib
import traceback

import pymongo
from bson import json_util

from flask import Flask
from flask import request
from flask import render_template
from flask import url_for

import db

app = Flask(__name__)

def jsonify(stuff):
  return json.dumps(stuff,
                    default=json_util.default,
                    sort_keys = True,
                    indent = 2) + '\n'

def RemoveIds(data):
  if isinstance(data, list):
    return [RemoveIds(x) for x in data]
  else:
    try:
      if '_id' in data:
        del data['_id']
    except TypeError:
      pass

    return data

class RequestError(Exception):
  def __init__(self, status, msg):
    self.status = status
    self.msg = msg

  def __str__(self):
    return "%s (%d)" % (self.msg, self.status)

api_boolean = {'oui': True, 'non': False}

"""
Méthode déclarative pour décrire les arguments nécessaires pour la
création/modification de chaque type de ressource de l'API.

Ce tableau est utilisé principalement par ParseIncoming().

Pour chaque clé (p.e. 'membres'), on a:
  * required: liste de clés nécessaires lors de la création (POST)
  * optional: liste de clés optionnelles
  * valid: dict avec les noms de paramètres comme clés.
           Si la valeur est une liste, la valeur fournie par le client
           doit se trouver dans cette liste pour être valide. S'il
           s'agit d'un objet "callable", celui-ci est appelé et doit
           retourner True ou False pour indiquer si la valeur est
           valide. Si la valeur est un dict, la valeur fournie par le
           client doit se trouver dans la liste de clés du dict pour
           être valide.
  * transform: dict avec les noms de paramètres comme clés.
               Si la valeur est un dict, celui-ci est utilisé pour faire
               la transformation (le paramètre est utilisé comme clé
               pour déduire la valeur transformée). Si la valeur est un
               objet "callable", celui-ci est appelé et doit retourner
               la valeur transformée.

Maybe TODO: peut-être qu'un seul callback qui fait validation + transform ce serait assez...
"""
validation = {
  'membres': {
    'req': ['prenom', 'nom'],
    'opt': ['courriel', 'listedenvoi', 'provenance', 'estbenevole', 'telephone'],
    'valid': {
      'listedenvoi': ['non', 'oui', 'fait'],
      'estbenevole': api_boolean
    },
    'transform': {
      'estbenevole': api_boolean
    }
  },
  'pieces': {
    'req': ['numero'],
    'opt': ['section', 'nom', 'reference', 'caracteristique', 'numerobabac', 'prixbabac', 'quantiteneuf', 'prixneuf', 'quantiteusage', 'prixusage', 'remarques'],
    'valid': {
      'numero': unicode.isdigit,
      'numerobabac': unicode.isdigit,
      'prixneuf': unicode.isdigit,
      'prixusage': unicode.isdigit,
      'prixbabac': unicode.isdigit,
      'quantiteneuf': unicode.isdigit,
      'quantiteusage': unicode.isdigit,
    },
    'transform': {
      'numero': int,
      'numerobabac': int,
      'prixneuf': int,
      'prixusage': int,
      'prixbabac': int,
      'quantiteneuf': int,
      'quantiteusage': int,
    }
  },
  'factures': {
    'req': ['membre'],
    'opt': ['benevole', 'fermee'],
    'valid': {
      'membre': unicode.isdigit,
      'benevole': unicode.isdigit,
      'fermee': api_boolean,
    },
    'transform': {
      'membre': int,
      'benevole': int,
      'fermee': api_boolean,
    }
  },
}

"""
  Throws RequestError if missing parameter/wrong value.
"""
def ParseIncoming(data, collection_name, throw_if_required_missing = True):
  def ValidateValue(valid, key, value):
    if key in valid:
      validate = valid[key]
      if hasattr(validate, '__call__'):
        if not validate(value):
          raise RequestError(httplib.BAD_REQUEST, "Valeur invalide pour %s" % key)
      elif isinstance(validate, list) or isinstance(validate, dict):
        if not value in validate:
          raise RequestError(httplib.BAD_REQUEST, "Valeur invalide pour %s" % key)

  def TransformValue(transformations, key, value):
    if key in transformations:
      transformation = transformations[key]
      if hasattr(transformation, '__call__'):
        return transformation(value)
      elif isinstance(transformation, dict):
        return transformation[value]

    return value

  v = validation[collection_name] if collection_name in validation else {}
  required_keys = v['req'] if 'req' in v else {}
  optional_keys = v['opt'] if 'opt' in v else {}
  valid = v['valid'] if 'valid' in v else {}
  transform = v['transform'] if 'transform' in v else {}

  ret = {}

  for key in required_keys:
    if key in data:
      value = data[key]
      ValidateValue(valid, key, value)
      ret[key] = TransformValue(transform, key, value)
    elif throw_if_required_missing:
      raise RequestError(httplib.BAD_REQUEST, "Parametre manquant: %s" % key)

  for key in optional_keys:
    if key in data:
      value = data[key]
      ValidateValue(valid, key, value)
      ret[key] = TransformValue(transform, key, value)

  return ret

# dev
@app.route('/api/dev/drop', methods=['GET'])
def Drop():
  db.DBConnection().membres.remove()
  db.DBConnection().pieces.remove()
  db.DBConnection().facture.remove()

  return "ok"

# api

"""
Les handlers sont généralement organisés comme ceci (certaines étapes
sont parfois omises):
1- Vérifier si la resource existe vraiment, sinon lancer un 404.
2- Décoder les paramètres fournis par le client et lancer un 400 si des
   paramètres sont manquants ou invalides (fait par ParseIncoming).
3- Ajouter des données supplémentaires au besoin, comme le datetime
   actuel, par exemple.
4- Faire une vérifications "sémantique". Par exemple, vérifier que pour
   un champ qui représente un # de membre, ce membre existe bel et bien.
5- Faire l'opération demandée (GET, POST, PUT ou DELETE)
"""
@app.route('/api/membres', methods=['GET'])
def GetMembres():
  result = {}
  status = 200
  headers = {'Content-type': 'application/json'}

  try:
    result = RemoveIds(list(db.DBConnection().membres.find()))
  except Exception as e:
    result = str(e)
    status = 500

  return jsonify(result), status, headers

@app.route('/api/membres', methods=['POST'])
def PostMembres():
  membre = {}
  headers = {}

  result = None
  status = 201

  try:
    membre = ParseIncoming(request.form, 'membres')

    membre['numero'] = ObtenirProchainNumeroDeMembre()
    membre['dateinscription'] = datetime.now()

    db.DBConnection().membres.insert(membre)

    headers['Location'] = url_for('GetMembresNumero', numero = membre['numero'])

    result = {'numero': membre['numero']}

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as ex:
    status = 500
    result = str(ex)

  return jsonify(result), status, headers

@app.route('/api/membres/<int:numero>', methods=['PUT'])
def PutMembres(numero):
  result = {}
  status = 200

  try:
    membre = ParseIncoming(request.form, 'membres', False)

    update_result = db.DBConnection().membres.update(
        {'numero': numero},
        {'$set': membre},
        safe = True
    )

    if not update_result['updatedExisting']:
      status = 404
      result = str('Membre inexistant')

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as ex:
    status = 500
    result = str(ex)
    traceback.print_exc()

  return jsonify(result), status

@app.route('/api/membres/<int:numero>', methods=['DELETE'])
def DeleteMembres(numero):
  result = ''
  status = 204

  try:
    db.DBConnection().membres.remove({'numero': numero})
  except Exception as ex:
    status = 500
    result = str(ex)

  return jsonify(result), status


@app.route('/api/membres/<int:numero>', methods=['GET'])
def GetMembresNumero(numero):
  result = {}
  status = 200

  try:
    result = db.DBConnection().membres.find_one({'numero': numero})
    if result is None:
      result = {'error': 'Ce membre n\'existe pas'}
      status = 404
  except Exception as e:
    result = str(e)
    status = 200

  return jsonify(result), status

# api pieces
@app.route('/api/pieces', methods=['GET'])
def GetPieces():
  result = {}
  status = 200

  try:
    result = RemoveIds(list(db.DBConnection().pieces.find()))

  except Exception as e:
    result = str(e)
    status = 500

  return jsonify(result), status

@app.route('/api/pieces', methods=['POST'])
def PostPieces():
  result = {}
  status = httplib.CREATED
  headers = {}

  try:
    piece = ParseIncoming(request.form, 'pieces')

    if PieceExiste(piece['numero']):
      raise RequestError(httplib.CONFLICT, 'Ce numero de piece est deja pris')

    db.DBConnection().pieces.insert(piece)

    headers['Location'] = url_for('GetPiecesNumero', numero = piece['numero'])

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as ex:
    status = httplib.INTERNAL_SERVER_ERROR
    result = str(ex)

  return jsonify(result), status, headers

@app.route('/api/pieces/<int:numero>', methods=['PUT'])
def PutPieces(numero):
  result = {}
  status = httplib.NO_CONTENT

  try:
    if not PieceExiste(numero):
      raise RequestError(httplib.NOT_FOUND, "Cette pièce n'existe pas.")

    piece = ParseIncoming(request.form, 'pieces', False)

    if PieceExiste(piece['numero']) and numero != piece['numero']:
      raise RequestError(httplib.CONFLICT, 'Ce numero de piece est deja pris')

    update_result = db.DBConnection().pieces.update(
        {'numero': numero},
        {'$set': piece}
    )

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as ex:
    status = 500
    result = str(ex)

  return jsonify(result), status

@app.route('/api/pieces/<int:numero>', methods=['DELETE'])
def DeletePieces(numero):
  result = ''
  status = 204

  try:
    db.DBConnection().pieces.remove({'numero': numero})
  except Exception as ex:
    status = 500
    result = str(ex)

  return jsonify(result), status

@app.route('/api/pieces/<int:numero>', methods=['GET'])
def GetPiecesNumero(numero):
  result = {}
  status = 200

  try:
    result = db.DBConnection().pieces.find_one({'numero': numero})
    if result is None:
      result = {'error': 'Cette piece n\'existe pas'}
      status = 404

    result = RemoveIds(result)

  except Exception as e:
    result = str(e)
    status = 200

  return jsonify(result), status

@app.route('/api/factures', methods=['GET'])
def GetFactures():
  result = {}
  status = 200

  try:
    result = RemoveIds(list(db.DBConnection().factures.find()))

  except Exception as e:
    result = str(e)
    status = 500

  return jsonify(result), status

def ValidationFactures(facture):
  if 'membre' in facture and not MembreExiste(facture['membre']):
    raise RequestError(httplib.UNPROCESSABLE_ENTITY, "Ce membre n'existe pas.")

  if 'benevole' in facture and not EstBenevole(facture['benevole']):
    raise RequestError(httplib.UNPROCESSABLE_ENTITY, "Ce benevole n'existe pas.")

@app.route('/api/factures', methods=['POST'])
def PostFactures():
  facture = {}
  headers = {}

  result = {}
  status = httplib.CREATED

  try:
    facture = ParseIncoming(request.form, 'factures')

    facture['numero'] = ObtenirProchainNumeroDeFacture()
    facture['date'] = datetime.now()

    ValidationFactures(facture)

    db.DBConnection().factures.insert(facture)
    headers['Location'] = url_for('GetFacturesNumero', numero=facture['numero'])
    result = {'numero': facture['numero']}

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as ex:
    status = 500
    result = str(ex)

  return jsonify(result), status, headers

@app.route('/api/factures/<int:numero>', methods=['PUT'])
def PutFactures(numero):
  result = {}
  status = httplib.NO_CONTENT

  try:
    facture = ParseIncoming(request.form, 'factures', False)

    ValidationFactures(facture)

    update_result = db.DBConnection().factures.update(
        {'numero': numero},
        {'$set': facture},
        safe = True
    )

    if not update_result['updatedExisting']:
      status = httplib.NOT_FOUND
      result = str('Facture inexistante')

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as ex:
    status = httplib.INTERNAL_SERVER_ERROR
    result = str(ex)

  return jsonify(result), status

@app.route('/api/factures/<int:numero>', methods=['DELETE'])
def DeleteFactures(numero):
  result = ''
  status = 204

  try:
    db.DBConnection().factures.remove({'numero': numero})
  except Exception as ex:
    status = 500
    result = str(ex)

  return jsonify(result), status

@app.route('/api/factures/<int:numero>', methods=['GET'])
def GetFacturesNumero(numero):
  result = {}
  status = 200

  try:
    result = db.DBConnection().factures.find_one({'numero': numero})
    if result is None:
      result = {'error': 'Cette facture n\'existe pas'}
      status = 404

    result = RemoveIds(result)

  except Exception as e:
    result = str(e)
    status = 200

  return jsonify(result), status


# Helper
def MembreExiste(numero):
  return db.DBConnection().membres.find_one({'numero': numero}) != None

def PieceExiste(numero):
  return db.DBConnection().pieces.find_one({'numero': numero}) != None

def EstBenevole(numero):
  membre = db.DBConnection().membres.find_one({'numero': numero, 'estbenevole': True})
  return membre != None

# l'app web
@app.route('/membres/', methods=['GET'])
def ListeMembres():
  return render_template('membres.html')

@app.route('/membres/<int:numero>', methods=['GET'])
def UnMembre(numero):
  membre =  db.DBConnection().membres.find_one({'numero': numero})
  return render_template('membre.html', numero=numero, membre=membre)

@app.route('/pieces/', methods=['GET'])
def ListePieces():
  return render_template('pieces.html')

@app.route('/pieces/<int:numero>', methods=['GET'])
def UnePiece():
  return render_template('piece.html')

@app.route('/caisse', methods=['GET'])
def Caisse():
  return render_template('caisse.html')

# TODO: replace by http://docs.mongodb.org/manual/tutorial/create-an-auto-incrementing-field/
def ObtenirProchainNumeroDeMembre():
  """Retourne le prochain numero de membre disponible."""
  d = db.DBConnection()

  if d.membres.count() == 0:
    return 1
  else:
    return d.membres.find().sort('numero', pymongo.DESCENDING).limit(1)[0]['numero'] + 1

def ObtenirProchainNumeroDeFacture():
  """Retourne le prochain numero de facture disponible."""
  d = db.DBConnection()

  if d.factures.count() == 0:
    return 1
  else:
    return d.factures.find().sort('numero', pymongo.DESCENDING).limit(1)[0]['numero'] + 1


if __name__ == '__main__':
  if 'BICIKLO_DEBUG' in os.environ:
    app.debug = True

  app.run(host='0.0.0.0', port = 8888)
