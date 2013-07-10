from datetime import datetime
import json
import os
import time
import httplib

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

validation = {
  'membres': {
    'required': ['prenom', 'nom'],
    'optional': ['courriel', 'listedenvoi', 'provenance'],
    'valid': {
      'listedenvoi': ['non', 'oui', 'fait']
    }
  },
  'pieces': {
    'required': ['numero'],
    'optional': ['section', 'nom', 'reference', 'caracteristique'],
    'valid': {
      'numero': unicode.isdigit
    }
  }
}


"""
  Throws KeyError if required key is not present.
  Throws ValueError if value is not valid.
"""
def ParseIncoming(data, collection_name, throw_if_required_missing = True):
  def ValidateValue(valid_values, key, value):
    if key in valid_values:
      valid = valid_values[key]
      if hasattr(valid, '__call__'):
        if not valid(value):
          raise ValueError(key)
      elif isinstance(valid, list):
        if not value in valid:
          raise ValueError(key)

  if collection_name in validation:
    required_keys = validation[collection_name]['required']
    optional_keys = validation[collection_name]['optional']
    valid_values  = validation[collection_name]['valid']
  else:
    required_keys = {}
    optional_keys = {}
    valid_values = {}

  ret = {}

  for key in required_keys:
    if key in data or throw_if_required_missing:
      value = data[key]
      ValidateValue(valid_values, key, value)
      ret[key] = value

  for key in optional_keys:
    if key in data:
      value = data[key]
      ValidateValue(valid_values, key, value)
      ret[key] = value

  return ret


# api membres
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
    
    headers['Location'] = url_for('PostMembres') + "/" + membre['numero']

    result = {'numero': membre['numero']}

  except KeyError as ex:
    status = 400
    result = 'Parametre manquant: %s.' % ex.message
  except ValueError as ex:
    status = 400
    result = 'Valeur invalide pour %s.' % ex.message
  except Exception as ex:
    status = 500
    result = str(ex)

  return jsonify(result), status
  
@app.route('/api/membres/<int:numero>', methods=['PUT'])
def PutMembre(numero):
  result = {}
  status = 200

  try:
    valeurs = ParseIncoming(request.form, 'membres', False)

    update_result = db.DBConnection().membres.update(
        {'numero': numero},
        {'$set': valeurs},
        safe = True
    )

    if not update_result['updatedExisting']:
      status = 404
      result = str('Membre inexistant')

  except ValueError as ex:
    status = 400
    result = str('Valeur invalide pour %s' % ex.message)
  except Exception as ex:
    status = 500
    result = str(ex)

  return jsonify(result), status

@app.route('/api/membres/<int:numero>', methods=['DELETE'])
def DeleteMembre(numero):
  result = ''
  status = 204

  try:
    delete_result = db.DBConnection().membres.remove({'numero': numero}, w = 1)
  except Exception as ex:
    status = 500
    result = str(ex)

  return jsonify(result), status


@app.route('/api/membres/<int:numero>', methods=['GET'])
def GetMembreNumero(numero):
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
  print result
  status = httplib.CREATED
  headers = {}

  try:
    piece = ParseIncoming(request.form, 'pieces')

    db.DBConnection().pieces.insert(piece)

    numero = piece['numero']

    headers['Location'] = url_for('GetPieces') + '/' + str(numero)

  except KeyError as ex:
    status = httplib.BAD_REQUEST
    result = 'Parametre manquant: %s.' % ex.message
  except ValueError as ex:
    status = httplib.BAD_REQUEST
    result = 'Valeur invalide pour %s.' % ex.message
  except Exception as ex:
    status = httplib.INTERNAL_SERVER_ERROR
    result = str(ex)

  return jsonify(result), status, headers

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

  app.run(host='0.0.0.0', port = 8888)
