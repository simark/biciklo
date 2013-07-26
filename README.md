biciklo
=======

Système d'inventaire pour l'atelier Biciklo.

Avant de démarrer :

	$ cd sass
	$ compass compile

Pour démarrer:
* Installer mongodb
* Démarrer mongodb
* Cloner l'entrepôt
* BICIKLO_DEBUG python index.py

index.py va imprimer l'adresse pour accéder au site avec le fureteur

Exemples d'utilisation de curl pour débugger l'API HTTP:
* Liste de factures: curl -X GET http://0.0.0.0:8888/api/factures
* Liste de membres: curl -X GET http://0.0.0.0:8888/api/membres
* Ajout d'un membre: curl -X POST --data "prenom=bob&nom=leponge" http://0.0.0.0:8888/api/membres
* Suppression d'un membre: curl -X DELETE http://0.0.0.0:8888/api/membres/6
