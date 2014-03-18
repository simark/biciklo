# -*- coding: utf-8 -*-
import sys
python_major = sys.version_info.major

import datetime
import json
import os
import time

if python_major == 2:
  import httplib
elif python_major == 3:
  import http.client as httplib

import pymongo
from bson import json_util

from flask import Flask
from flask import request
from flask import render_template
from flask import url_for

import db

app = Flask(__name__)

# numéro de pièce des abonnements et durées
abonnements = {
  # Annuel
  100: datetime.timedelta(days = 364),
  # Mensuel
  200: datetime.timedelta(days = 30),
}

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

def FormatPrix(prix_cennes):
  piasses = prix_cennes / 100
  cennes = prix_cennes % 100
  return "%d.%02d $" % (piasses, cennes)

app.jinja_env.filters['formatprix'] = FormatPrix

class RequestError(Exception):
  def __init__(self, status, msg):
    self.status = status
    self.msg = msg

  def __str__(self):
    return "%s (%d)" % (self.msg, self.status)

api_boolean = {'oui': True, 'non': False}

def ValidationQuantite(quantite_str):
  try:
    val =  int(quantite_str)
  except ValueError as e:
    val = float(quantite_str)

  if val < 0:
    raise ValueError()

  return val

def ValidationEntierPositif(entier_str):
  i = int(entier_str)

  if i < 0:
    raise ValueError()

  return i

def ValidationDate(date_str):
  return datetime.datetime.strptime(date_str, "%Y-%m-%d")

"""
Méthode déclarative pour décrire les arguments nécessaires pour la
création/modification de chaque type de ressource de l'API.

Ce tableau est utilisé principalement par ParseIncoming().

Pour chaque clé (p.e. 'membres'), on a:
  * req: liste de clés nécessaires lors de la création (POST)
  * opt: liste de clés optionnelles
  * valid: Effectue la validation et la transformation des valeurs
           en entrée. Il doit s'agir d'un dict avec les noms de
           paramètres comme clés. Les valeurs peuvent être les
           suivantes:

           list: Pour être valide, la valeur doit se trouver dans la
                 liste. Aucune transformation n'est appliquée.

           dict: Pour être valide, la valeur en entrée doit être une clé
                 dans le dict (opérateur "in"). La valeur transformée
                 est la valeur correspondand à cette clé.

           fonction: La fonction est appelée avec la valeur, et doit
                     lever une exception ValueError pour indiquer une
                     valeur invalide. La valeur transformée correspond
                     à la valeur de retour de cette fonction.
"""
validation = {
  'membres': {
    'req': ['prenom', 'nom'],
    'opt': ['numero', 'courriel', 'listedenvoi', 'provenance', 'estbenevole', 'telephone', 'notes'],
    'valid': {
      'numero': ValidationEntierPositif,
      'listedenvoi': ['non', 'oui', 'fait'],
      'estbenevole': api_boolean
    }
  },
  'pieces': {
    'req': ['numero'],
    'opt': ['section', 'nom', 'reference', 'caracteristique', 'numerobabac', 'prixbabac', 'quantite', 'prix', 'remarques', 'active'],
    'valid': {
      'numero': ValidationEntierPositif,
      'prix': ValidationEntierPositif,
      'prixbabac': ValidationEntierPositif,
      'quantite': ValidationQuantite,
      'active': api_boolean,
    }
  },
  'factures': {
    'req': ['membre'],
    'opt': ['benevole', 'complete', 'date'],
    'valid': {
      'membre': ValidationEntierPositif,
      'benevole': ValidationEntierPositif,
      'complete': api_boolean,
      'date': ValidationDate,
    }
  },
  'factureajoutpiece': {
    'req': ['numero'],
    'opt': ['quantite', 'fusionsiexiste'],
    'valid': {
      'numero': ValidationEntierPositif,
      'quantite': ValidationQuantite,
      'fusionsiexiste': api_boolean,
    }
  },
  'heuresbenevole': {
    'req': ['heures', 'raison'],
    'opt': ['date'],
    'valid': {
      'heures': ValidationQuantite,
      'date': ValidationDate,
    }
  },
  'getfactures': {
    'opt': ['complete', 'membre', 'debut', 'fin'],
    'valid': {
      'complete': api_boolean,
      'membre': ValidationEntierPositif,
      'debut': ValidationDate,
      'fin': ValidationDate,
    }
  }
}

"""
  Analyse les paramètres fournis par le client.
  Lève un RequestError s'il y a une erreur de paramètres (manquants ou mauvaises valeurs).

  Variables d'entrée

      data
          dict. Données fournie en entrée par le client
      collection_name
          type de ressource à aller chercher dans le tableau 'validation'
          (exemple: 'membres', 'pieces', 'factures', ...)
      throw_if_required_missing
          bool. Si True, lève une exception s'il manque au moins un paramètre requis.

  Variable de sortie
      ret
          dict. data dont chaque valeur a posiblement été transformée par
          la fonction de validation.
"""
def ParseIncoming(data, collection_name, throw_if_required_missing = True):
  def ValidateAndTransformValue(validationArray, key, value):
    if key in validationArray:
      # Objet de validation correspondant au paramètre
      validate = validationArray[key]

      # validate est un objet "callable" (comme une fonction)...
      if hasattr(validate, '__call__'):
        try:
          return validate(value)
        except ValueError as e:
          raise RequestError(httplib.BAD_REQUEST, "Valeur invalide pour %s." %key)
      # ... ou une liste...
      elif isinstance(validate, list):
        if value in validate:
          return value
        else:
          raise RequestError(httplib.BAD_REQUEST, "Valeur invalide pour %s." %key)
      # ... ou un dictionnaire...
      elif isinstance(validate, dict):
        if value in validate:
          return validate[value]
        else:
          raise RequestError(httplib.BAD_REQUEST, "Valeur invalide pour %s" % key)

      # ... ou autre chose.
      return value

    # Pas de validation pour cette clé
    return value

  # v est un dictionnaire contenant, pour chaque paramètre valide pour
  # ce type de ressource, un dict avec les clés 'req', 'opt' et 'valid'
  v = validation[collection_name] if collection_name in validation else {}
  required_keys = v['req'] if 'req' in v else {}
  optional_keys = v['opt'] if 'opt' in v else {}
  validateCollection = v['valid'] if 'valid' in v else {}

  ret = {}

  # Teste les paramètres requis
  for key in required_keys:
    if key in data:
      value = data[key]
      ret[key] = ValidateAndTransformValue(validateCollection, key, value)
    elif throw_if_required_missing:
      # Lève une exception si le paramètre est manquant
      raise RequestError(httplib.BAD_REQUEST, "Parametre manquant: %s" % key)

  # Teste les paramètres optionnels
  for key in optional_keys:
    if key in data:
      value = data[key]
      ret[key] = ValidateAndTransformValue(validateCollection, key, value)

  return ret

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

    if 'numero' in membre:
      # Numéro de membre fourni par le client, vérifier qu'il n'est pas pris
      if ObtenirMembre(membre['numero']) != None:
        raise RequestError(httplib.CONFLICT, "Ce numéro de membre est déjà pris.")
    else:
      # On attribut automatiquement un # de membre
      membre['numero'] = ObtenirProchainNumeroDeMembre()

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

@app.route('/api/benevoles', methods=['GET'])
def GetBenevoles():
  result = {}
  status = httplib.OK
  headers = {'Content-type': 'application/json'}

  try:
    result = list(db.DBConnection().membres.find({'estbenevole': True}))

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as e:
    result = str(e)
    status = httplib.INTERNAL_SERVER_ERROR

  return jsonify(result), status, headers

@app.route('/api/membres/<int:numero>/heuresbenevoles', methods=['POST'])
def PostHeuresBenevoles(numero):
  result = {}
  status = httplib.CREATED
  headers = {'Content-type': 'application/json'}

  try:
    heures = ParseIncoming(request.form, 'heuresbenevole')

    if not EstBenevole(numero):
      raise RequestError(httplib.UNPROCESSABLE_ENTITY, 'Ce membre n\'est pas bénévole')

    if 'date' not in heures:
      heures['date'] = datetime.datetime.now()

    db.DBConnection().membres.update({"numero":  numero},
        {'$push': {"heuresbenevole": heures}})

  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as ex:
    status = httplib.INTERNAL_SERVER_ERROR
    result = str(ex)

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

    # Si changement de numéro, vérifier que le numéro n'est pas déjà pris
    if 'numero' in piece and PieceExiste(piece['numero']) and numero != piece['numero']:
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
  headers = {'Content-type': 'application/json'}

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

  return jsonify(result), status, headers

@app.route('/api/categoriespieces', methods=['GET'])
def GetCategoriesPieces():
  result = {}
  status = httplib.OK
  headers = {'Content-type': 'application/json'}

  try:
    categories = list(db.DBConnection().pieces.distinct('section'));
    categories.sort()

    result = categories

  except Exception as e:
    result = str(e)
    status = httplib.INTERNAL_SERVER_ERROR

  return jsonify(result), status, headers

@app.route('/api/factures', methods=['GET'])
def GetFactures():
  result = {}
  status = httplib.OK
  headers = {'Content-type': 'application/json'}

  try:
    filters = ParseIncoming(request.args, 'getfactures')

    debut = filters.pop('debut', None)
    fin = filters.pop('fin', None)

    if debut or fin:
      filters['date'] = {}

      if debut:
        filters['date']['$gte'] = debut

      if fin:
        filters['date']['$lte'] = fin

    result = list(db.DBConnection().factures.find(filters).sort('numero', 1))

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
    facture['pieces'] = []

    facture['prixtotal'] = 0

    if 'complete' not in facture:
      facture['complete'] = False

    if 'date' not in facture:
      facture['date'] = datetime.datetime.now()

    ValidationFactures(facture)

    db.DBConnection().factures.insert(facture)
    headers['Location'] = url_for('GetFacturesNumero', numero=facture['numero'])
    result = facture

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

@app.route('/api/factures/<int:numero>', methods=['DELETE'])
def DeleteFactures(numero):
  result = ''
  status = httplib.NO_CONTENT

  try:
    facture = ObtenirFacture(numero)
    mettreAJourAbonnement = False

    if not facture:
      raise RequestError(httplib.NOT_FOUND, "Cette facture n'existe pas")

    if 'pieces' in facture:
      lignes = facture['pieces']
      for ligne in lignes:
        AjouterQuantitePieces(ligne)

        if ligne['numero'] in abonnements:
          mettreAJourAbonnement = True

    # Supprimer la facture
    db.DBConnection().factures.remove({'numero': numero})

    # Mettre à jour l'abonnement au besoin
    if mettreAJourAbonnement:
      MettreAJourExpirationMembre(facture['membre'])

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
  headers = {'Content-type': 'application/json'}

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

  return jsonify(result), status, headers

def TraiterQuantitesAjoutPieceFacture(valeurs, piece):
  entree_piece = {}
  prix_total = 0

  if 'prix' not in piece:
    raise RequestError(httplib.UNPROCESSABLE_ENTITY, "Impossible d'ajouter la pièce à la facture, elle ne possède pas de prix.")

  entree_piece['prix'] = piece['prix']
  entree_piece['quantite'] = valeurs['quantite']

  entree_piece['prixtotal'] = CalculerPrixTotalEntreePiece(entree_piece)
  entree_piece['numero'] = piece['numero']

  return entree_piece

# Ajoute le contenu de entree_piece à celui de entree_piece_existante
def FusionEntreesPieces(entree_piece_existante, entree_piece):
  assert entree_piece_existante['numero'] == entree_piece['numero']

  # Vérifier que le prix n'a pas changé
  if entree_piece_existante['prix'] != entree_piece['prix']:
    raise RequestError(httplib.CONFLICT, "Cette facture contient déjà cette pièce, mais avec un prix différent")

  entree_piece_existante['quantite'] +=  entree_piece['quantite']

  entree_piece_existante['prixtotal'] = CalculerPrixTotalEntreePiece(entree_piece_existante)

# Ajoute les quantités à l'inventaire à partir d'une entrée pièce d'une facture
def AjouterQuantitePieces(entree_piece):
  numero_piece = entree_piece['numero']

  if numero_piece in abonnements:
    return

  quantite = entree_piece['quantite']
  db.DBConnection().pieces.update({'numero': numero_piece}, {'$inc': {'quantite': quantite}})

# Soustrait les quantités de l'inventaire à partir d'une entrée pièce d'une facture
def SoustraireQuantitePieces(entree_piece):
  numero_piece = entree_piece['numero']

  if numero_piece in abonnements:
    return

  quantite = entree_piece['quantite']
  db.DBConnection().pieces.update({'numero': numero_piece}, {'$inc': {'quantite': -quantite}})

# Calcule le prix total de la facture, en cents. Arrondit le montant
# final au 25 cents le plus près.
def CalculerPrixTotalFacture(facture):
  total = 0

  if 'pieces' in facture:
    lignesFacture = facture['pieces']

    for ligne in lignesFacture:
      total += ligne['prixtotal']

  # Arrondir au 25 cents
  rem = total % 25
  if rem >= 13:
    total = total - rem + 25
  else:
    total = total - rem

  return total

# Calcule le prix total d'une entrée d'une pièce dans une facture.
def CalculerPrixTotalEntreePiece(entree_piece):
  return int(entree_piece['quantite'] * entree_piece['prix'])

@app.route('/api/factures/<int:numero_facture>/pieces', methods=['POST'])
def PostPieceInFacture(numero_facture):
  result = {}
  status = httplib.OK
  headers = {'Content-type': 'application/json'}

  try:
    if not FactureExiste(numero_facture):
      raise RequestError(httplib.NOT_FOUND, "Cette facture n'existe pas.")

    facture = ObtenirFacture(numero_facture)

    val = ParseIncoming(request.form, 'factureajoutpiece')
    numero_piece = val['numero']

    if not PieceExiste(numero_piece):
      raise RequestError(httplib.UNPROCESSABLE_ENTITY, "Cette pièce n'existe pas.")

    entree_piece_existante = None

    if 'pieces' in facture:
      for ep in facture['pieces']:
        if ep['numero'] == numero_piece:
          if 'fusionsiexiste' in val and val['fusionsiexiste']:
            entree_piece_existante = ep
          else:
            raise RequestError(httplib.CONFLICT, "Cette pièce est déjà présente dans cette facture.")

    piece = ObtenirPiece(numero_piece)

    entree_piece = TraiterQuantitesAjoutPieceFacture(val, piece)

    if entree_piece_existante is None:
      # Ajouter la pièce dans la facture
      facture['pieces'].append(entree_piece)
      result = entree_piece
    else:
      # Ajouter les quantités à l'entrée existante
      # entree_piece_existante étant une référence, ça modifie directement dans la liste facture['pieces']
      FusionEntreesPieces(entree_piece_existante, entree_piece)
      result = entree_piece_existante

    # Ajuster le prix total de la facture
    facture['prixtotal'] = CalculerPrixTotalFacture(facture)

    # Écrire la facture dans la BD
    db.DBConnection().factures.update({'numero': numero_facture}, facture)

    # Ajuster les quantités en inventaire
    SoustraireQuantitePieces(entree_piece)

    # Mise à jour de la date d'abonnement, si requis
    if numero_piece in abonnements:
      MettreAJourExpirationMembre(facture['membre'])



  except RequestError as ex:
    status = ex.status
    result = ex.msg
  except Exception as e:
    result = str(e)
    status = httplib.INTERNAL_SERVER_ERROR

  return jsonify(result), status, headers

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

    # Supprimer la pièce de la facture
    facture['pieces'] = [x for x in facture['pieces'] if x['numero'] != numero_piece]

    # Ajuster le prix total de la facture
    facture['prixtotal'] = CalculerPrixTotalFacture(facture)

    # Écrire la facture dans la BD
    db.DBConnection().factures.update({'numero': numero_facture}, facture)

    # Ajuster les quantités en inventaire
    AjouterQuantitePieces(entree_piece)

    # Mise à jour de la date d'abonnement, si requis
    if numero_piece in abonnements:
      MettreAJourExpirationMembre(facture['membre'])

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

def CalculerExpirationMembre(numero):
  if not MembreExiste(numero):
    raise ValueError('Membre inexistant')

  factures = db.DBConnection().factures.find({'membre': numero})

  latest = None
  for facture in factures:
    if 'pieces' not in facture:
      continue
    for ligne in facture['pieces']:
      if ligne['numero'] in abonnements:
        tentative = facture['date'] + abonnements[ligne['numero']]
        if latest is None or tentative > latest:
          latest = tentative

  return latest

def MettreAJourExpirationMembre(numero):
  exp = CalculerExpirationMembre(numero)

  db.DBConnection().membres.update({'numero': numero}, {'$set': {'expiration': exp}})


# l'app web

#appellé lorsqu'on va à la racine de la page web. C'est-à-dire http://0.0.0.0:8888/
@app.route('/', methods=['GET'])
def Index():
  return render_template('index.html')

#appelé lorsqu'on va sur la page "Liste des membres"
@app.route('/membres/', methods=['GET'])
def ListeMembres():
  return render_template('membres.html')

@app.route('/membres/<int:numero>', methods=['GET'])
def UnMembre(numero):
  membre =  db.DBConnection().membres.find_one({'numero': numero})
  return render_template('membre.html', numero=numero, membre=membre)

#appelé lorsqu'on va sur la page "Liste des pièces"
@app.route('/pieces/', methods=['GET'])
def ListePieces():
  return render_template('pieces.html')

@app.route('/pieces/<int:numero>', methods=['GET'])
def UnePiece(numero):
  piece = ObtenirPiece(numero)
  return render_template('piece.html', piece = piece)

#appelé lorsqu'on va sur la page "Factures"
@app.route('/factures', methods=['GET'])
def Factures():
  return render_template('factures.html')

@app.route('/factures-fermees', methods=['GET'])
def FacturesFermees():
  factures = list(db.DBConnection().factures.find({'complete': True}))
  membres = {}

  for facture in factures:
    if facture['membre'] not in membres:
      membres[facture['membre']] = ObtenirMembre(facture['membre'])

  return render_template('factures-fermees.html', factures = factures, membres = membres)

#appelé lorsqu'on va sur la page correspondant à h
@app.route('/heuresbenevoles', methods=['GET'])
def HeuresBenevoles():
  benevoles = list(db.DBConnection().membres.find({'estbenevole': True}).sort('prenom', pymongo.ASCENDING))

  return render_template('heuresbenevoles.html', benevoles = benevoles)

#appelé lorsqu'on va sur la page correspondant à "Admin"
@app.route('/admin', methods=['GET'])
def Admin():
  return render_template('admin.html')

@app.route('/admin/rapport', methods=['GET'])
def AdminRapport():
  # (année, mois) -> ($ pièces, $ abonnements)
  somme_ventes = {}

  factures = db.DBConnection().factures.find()

  for facture in factures:
    mois = (facture['date'].year, facture['date'].month)
    somme_pieces = facture['prixtotal']
    somme_abonnements = 0

    for piece in facture['pieces']:

      if piece['numero'] in abonnements:
        somme_pieces -= piece['prixtotal']
        somme_abonnements += piece['prixtotal']

    ancien = somme_ventes.get(mois, (0, 0))
    somme_ventes[mois] = (ancien[0] + somme_pieces, ancien[1] + somme_abonnements)

  somme_ventes = sorted(somme_ventes.items())

  return render_template('admin-rapport.html', somme_ventes = somme_ventes)

@app.route('/admin/ventes', methods=['GET'])
def AdminVentes():
  return render_template('admin-ventes.html')

@app.route('/admin/listediffusion', methods=['GET'])
def AdminListeDiffusion():
  membres = db.DBConnection().membres.find({'listedenvoi': 'oui'})

  return render_template('admin-listediffusion.html', membres = list(membres))

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
