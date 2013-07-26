biciklo
=======

Système d'inventaire pour l'atelier Biciklo.

Pour démarrer:
* Installer les dépendances (voir plus loin)
* Cloner l'entrepôt
* Démarrer mongodb
* BICIKLO_DEBUG=1 python index.py

index.py va imprimer l'adresse pour accéder au site avec le fureteur

Exemples d'utilisation de curl pour débugger l'API HTTP:
* Liste de factures: curl -X GET http://0.0.0.0:8888/api/factures
* Liste de membres: curl -X GET http://0.0.0.0:8888/api/membres
* Ajout d'un membre: curl -X POST --data "prenom=bob&nom=leponge" http://0.0.0.0:8888/api/membres
* Suppression d'un membre: curl -X DELETE http://0.0.0.0:8888/api/membres/6

Dépendances:
* MongoDB (http://www.mongodb.org/)

Dépendances Python:
* Python 2, pour l'instant
* flask (http://flask.pocoo.org/)
* pymongo (http://api.mongodb.org/python/current/)
