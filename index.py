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
  stuff = RemoveIds(stuff)
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
    'opt': ['benevole', 'complete'],
    'valid': {
      'membre': unicode.isdigit,
      'benevole': unicode.isdigit,
      'complete': api_boolean,
    },
    'transform': {
      'membre': int,
      'benevole': int,
      'complete': api_boolean,
    }
  },
  'factureajoutpiece': {
    'req': ['numero'],
    'opt': ['quantiteneuf', 'quantiteusage'],
    'valid': {
      'numero': unicode.isdigit,
      'quantiteneuf': unicode.isdigit,
      'quantiteusage': unicode.isdigit,
    },
    'transform': {
      'numero': int,
      'quantiteneuf': int,
      'quantiteusage': int,
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
  status = httplib.OK
  headers = {'Content-type': 'application/json'}

  try:
    result = list(db.DBConnection().membres.find())
  except Exception as e:
    result = str(e)
    status = httplib.INTERNAL_SERVER_ERROR

  return jsonify(result), status, headers

@app.route('/api/membres', methods=['POST'])
def PostMembres():
  membre = {}
  headers = {}

  result = None
  status = httplib.CREATED

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
    status = httplib.INTERNAL_SERVER_ERROR
    result = str(ex)

  return jsonify(result), status, headers

@app.route('/api/membres/<int:numero>', methods=['PUT'])
def PutMembres(numero):
  result = {}
  status = httplib.OK

  try:
    if not MembreExiste(numero):
      raise RequestError(httplib.NOT_FOUND, "Ce membre n'existe pas")

    membre = ParseIncoming(request.form, 'membres', False)

    update_result = db.DBConnection().membres.update(
        {'numero': numero},
        {'$set': membre}
    )

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as ex:
    status = httplib.INTERNAL_SERVER_ERROR
    result = str(ex)

  return jsonify(result), status

# TODO: est-ce qu'on veut vraiment ça?
@app.route('/api/membres/<int:numero>', methods=['DELETE'])
def DeleteMembres(numero):
  result = ''
  status = httplib.NO_CONTENT

  try:
    db.DBConnection().membres.remove({'numero': numero})
  except Exception as ex:
    status = httplib.INTERNAL_SERVER_ERROR
    result = str(ex)

  return jsonify(result), status


@app.route('/api/membres/<int:numero>', methods=['GET'])
def GetMembresNumero(numero):
  result = {}
  status = httplib.OK
  headers = {'Content-type': 'application/json'}

  try:
    if not MembreExiste(numero):
      raise RequestError(httplib.NOT_FOUND, "Ce membre n'existe pas.")

    result = db.DBConnection().membres.find_one({'numero': numero})

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as e:
    result = str(e)
    status = httplib.INTERNAL_SERVER_ERROR

  return jsonify(result), status, headers

# api pieces
@app.route('/api/pieces', methods=['GET'])
def GetPieces():
  result = {}
  status = httplib.OK
  headers = {'Content-type': 'application/json'}

  try:
    result = list(db.DBConnection().pieces.find())

  except Exception as e:
    result = str(e)
    status = httplib.INTERNAL_SERVER_ERROR

  return jsonify(result), status, headers

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
    status = httplib.INTERNAL_SERVER_ERROR
    result = str(ex)

  return jsonify(result), status

# TODO: est-ce qu'on veut vraiment ça?
@app.route('/api/pieces/<int:numero>', methods=['DELETE'])
def DeletePieces(numero):
  result = ''
  status = httplib.NO_CONTENT

  try:
    db.DBConnection().pieces.remove({'numero': numero})
  except Exception as ex:
    status = httplib.INTERNAL_SERVER_ERROR
    result = str(ex)

  return jsonify(result), status

@app.route('/api/pieces/<int:numero>', methods=['GET'])
def GetPiecesNumero(numero):
  result = {}
  status = httplib.OK

  try:
    if not PieceExiste(numero):
      raise RequestError(httplib.NOT_FOUND, "Cette pièce n'existe pas.")

    result = db.DBConnection().pieces.find_one({'numero': numero})

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as e:
    result = str(e)
    status = httplib.INTERNAL_SERVER_ERROR

  return jsonify(result), status

@app.route('/api/factures', methods=['GET'])
def GetFactures():
  result = {}
  status = httplib.OK
  headers = {'Content-type': 'application/json'}

  try:
    result = list(db.DBConnection().factures.find())

  except Exception as e:
    result = str(e)
    status = httplib.INTERNAL_SERVER_ERROR

  return jsonify(result), status, headers

def ValidationFactures(facture):
  if 'membre' in facture and not MembreExiste(facture['membre']):
    raise RequestError(httplib.UNPROCESSABLE_ENTITY, "Ce membre n'existe pas.")

  if 'benevole' in facture and not EstBenevole(facture['benevole']):
    raise RequestError(httplib.UNPROCESSABLE_ENTITY, "Ce benevole n'existe pas.")

@app.route('/api/factures', methods=['POST'])
def PostFactures():
  facture = {}
  headers = {'Content-type': 'application/json'}

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
    status = httplib.INTERNAL_SERVER_ERROR
    result = str(ex)

  return jsonify(result), status, headers

@app.route('/api/factures/<int:numero>', methods=['PUT'])
def PutFactures(numero):
  result = {}
  status = httplib.NO_CONTENT

  try:
    if not FactureExiste(numero):
      raise RequestError(httplib.NOT_FOUND, "Cette facture n'existe pas.")

    facture = ParseIncoming(request.form, 'factures', False)

    ValidationFactures(facture)

    update_result = db.DBConnection().factures.update(
        {'numero': numero},
        {'$set': facture},
    )

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as ex:
    status = httplib.INTERNAL_SERVER_ERROR
    result = str(ex)

  return jsonify(result), status

# TODO: est-ce qu'on veut vraiment ça?
@app.route('/api/factures/<int:numero>', methods=['DELETE'])
def DeleteFactures(numero):
  result = ''
  status = httplib.NO_CONTENT

  try:
    db.DBConnection().factures.remove({'numero': numero})

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as ex:
    status = httplib.INTERNAL_SERVER_ERROR
    result = str(ex)

  return jsonify(result), status

@app.route('/api/factures/<int:numero>', methods=['GET'])
def GetFacturesNumero(numero):
  result = {}
  status = httplib.OK

  try:
    if not FactureExiste(numero):
      raise RequestError(httplib.NOT_FOUND, "Cette facture n'existe pas.")

    result = ObtenirFacture(numero)

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as e:
    result = str(e)
    status = httplib.INTERNAL_SERVER_ERROR

  return jsonify(result), status

def TraiterQuantitesAjoutPieceFacture(valeurs, piece):
  entree_piece = {}

  if 'quantiteneuf' in valeurs:
    quantite_neuf = valeurs['quantiteneuf']
    if 'prixneuf' not in piece:
      raise RequestError(httplib.UNPROCESSABLE_ENTITY, "Cette pièce ne possède pas de prix neuf.")

    prix_neuf = piece['prixneuf']

    entree_piece['prixneuf'] = prix_neuf
    entree_piece['quantiteneuf'] = quantite_neuf

  if 'quantiteusage' in valeurs:
    quantite_usage = valeurs['quantiteusage']
    if 'prixusage' not in piece:
      raise RequestError(httplib.UNPROCESSABLE_ENTITY, "Cette pièce ne possède pas de prix usagé.")

    prix_usage = piece['prixusage']

    entree_piece['prixusage'] = prix_usage
    entree_piece['quantiteusage'] = quantite_usage

  return entree_piece

# Ajoute les quantités à l'inventaire à partir d'une entrée pièce d'une facture
def AjouterQuantitePieces(entree_piece):
  numero_piece = entree_piece['numero']
  if 'quantiteneuf' in entree_piece:
    quantiteneuf = entree_piece['quantiteneuf']
    db.DBConnection().pieces.update({'numero': numero_piece}, {'$inc': {'quantiteneuf': quantiteneuf}})

  if 'quantiteusage' in entree_piece:
    quantiteusage = entree_piece['quantiteusage']
    db.DBConnection().pieces.update({'numero': numero_piece}, {'$inc': {'quantiteusage': quantiteusage}})

# Soustrait les quantités de l'inventaire à partir d'une entrée pièce d'une facture
def SoustraireQuantitePieces(entree_piece):
  numero_piece = entree_piece['numero']
  if 'quantiteneuf' in entree_piece:
    quantiteneuf = entree_piece['quantiteneuf']
    db.DBConnection().pieces.update({'numero': numero_piece}, {'$inc': {'quantiteneuf': -quantiteneuf}})

  if 'quantiteusage' in entree_piece:
    quantiteusage = entree_piece['quantiteusage']
    db.DBConnection().pieces.update({'numero': numero_piece}, {'$inc': {'quantiteusage': -quantiteusage}})

@app.route('/api/factures/<int:numero_facture>/pieces', methods=['POST'])
def PostPieceInFacture(numero_facture):
  result = {}
  status = httplib.CREATED

  try:
    if not FactureExiste(numero_facture):
      raise RequestError(httplib.NOT_FOUND, "Cette facture n'existe pas.")

    facture = ObtenirFacture(numero_facture)

    val = ParseIncoming(request.form, 'factureajoutpiece')
    numero_piece = val['numero']

    if not PieceExiste(numero_piece):
      raise RequestError(httplib.UNPROCESSABLE_ENTITY, "Cette pièce n'existe pas.")

    if 'pieces' in facture:
      for ep in facture['pieces']:
        if ep['numero'] == numero_piece:
          raise RequestError(httplib.CONFLICT, "Cette pièce fait déjà partie de cette facture.")

    piece = ObtenirPiece(numero_piece)

    entree_piece = TraiterQuantitesAjoutPieceFacture(val, piece)
    entree_piece['numero'] = numero_piece

    db.DBConnection().factures.update({'numero': numero_facture},
      {'$push': {'pieces': entree_piece}})

    # Ajuster quantités en inventaire
    SoustraireQuantitePieces(entree_piece)

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as e:
    result = str(e)
    status = httplib.INTERNAL_SERVER_ERROR

  return jsonify(result), status

@app.route('/api/factures/<int:numero_facture>/pieces/<int:numero_piece>', methods=['PUT'])
def PutPieceInFacture(numero_facture, numero_piece):
  result = {}
  status = httplib.NO_CONTENT

  try:
    if not FactureExiste(numero_facture):
      raise RequestError(httplib.NOT_FOUND, "Cette facture n'existe pas.")

    facture = ObtenirFacture(numero_facture)

    if not PieceExiste(numero_piece):
      raise RequestError(httplib.NOT_FOUND, "Cette piece n'existe pas.")

    if 'pieces' not in facture:
      raise RequestError(httplib.NOT_FOUND, "Cette facture ne contient pas cette pièce.")

    entree_piece = None

    for ep in facture['pieces']:
      if ep['numero'] == numero_piece:
        entree_piece = ep
        break

    if entree_piece is None:
      raise RequestError(httplib.NOT_FOUND, "Cette facture ne contient pas cette pièce.")

    val = ParseIncoming(request.form, 'factureajoutpiece', False)

    piece = ObtenirPiece(numero_piece)

    entree_piece_new = TraiterQuantitesAjoutPieceFacture(val, piece)

    # Ajuster quantités en inventaire (remettre les pièces, anciennes quantités)
    AjouterQuantitePieces(entree_piece)

    entree_piece.update(entree_piece_new)

    # Ajuster quantités en inventaire (enlever les pièces, nouvelles quantités)
    SoustraireQuantitePieces(entree_piece)

    db.DBConnection().factures.update({'numero': numero_facture, 'pieces.numero': numero_piece},
      {'$set': {'pieces.$': entree_piece}})

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as ex:
    status = httplib.INTERNAL_SERVER_ERROR
    result = str(ex)

  return jsonify(result), status

@app.route('/api/factures/<int:numero_facture>/pieces/<int:numero_piece>', methods=['DELETE'])
def DeletePieceFromFacture(numero_facture, numero_piece):
  result = {}
  status = httplib.NO_CONTENT

  try:
    if not FactureExiste(numero_facture):
      raise RequestError(httplib.NOT_FOUND, "Cette facture n'existe pas.")

    facture = ObtenirFacture(numero_facture)

    if 'pieces' not in facture:
      raise RequestError(httplib.NOT_FOUND, "Cette facture ne contient pas cette pièce.")

    entree_piece = None

    for ep in facture['pieces']:
        if ep['numero'] == numero_piece:
          entree_piece = ep
          break

    if entree_piece is None:
      raise RequestError(httplib.NOT_FOUND, "Cette facture ne contient pas cette pièce.")

    AjouterQuantitePieces(entree_piece)

    db.DBConnection().factures.update({'numero': numero_facture}, {'$pull': {'pieces': {'numero': numero_piece}}})

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as e:
    result = str(e)
    status = httplib.INTERNAL_SERVER_ERROR

  return jsonify(result), status

# Helper
def MembreExiste(numero):
  return ObtenirMembre(numero) != None

def ObtenirMembre(numero):
  return db.DBConnection().membres.find_one({'numero': numero})

def PieceExiste(numero):
  return ObtenirPiece(numero) != None

def ObtenirPiece(numero):
  return db.DBConnection().pieces.find_one({'numero': numero})

def FactureExiste(numero):
  return ObtenirFacture(numero) != None

def ObtenirFacture(numero):
  return db.DBConnection().factures.find_one({'numero': numero})

def EstBenevole(numero):
  membre = db.DBConnection().membres.find_one({'numero': numero, 'estbenevole': True})
  return membre != None

# l'app web
@app.route('/', methods=['GET'])
def Index():
  return render_template('index.html')

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
