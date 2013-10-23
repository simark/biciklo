biciklo
=======

Système d'inventaire pour l'atelier **Biciklo**.

dépendances
-----------

* Ruby (pour Compass ci-dessous)
* Compass (`gem install compass`)
* MongoDB
* Python 2 et quelques modules:
 * `flask` (<http://flask.pocoo.org/>)
 * `pymongo` (<http://api.mongodb.org/python/current/>)
 * Si j'en ai oublié, dites moi le.

lancement
---------

Les dépendances ci-dessus doivent être satisfaites et le serveur MongoDB
doit être lancé.

Compiler le CSS :

	$ cd sass
	$ compass compile
	$ cd ..

Lancer le site Flask :

	$ BICIKLO_DEBUG=1 python index.py

`index.py` imprimera l'URL qui permet l'accès au site Web.


API HTTP
--------

Exemples d'utilisation de cURL pour déboguer l'API HTTP.

### Liste de factures

	$ curl -X GET http://0.0.0.0:8888/api/factures
	
### Liste de membres


	$ curl -X GET http://0.0.0.0:8888/api/membres
	
### Ajout d'un membre

	$ curl -X POST --data "prenom=bob&nom=leponge" http://0.0.0.0:8888/api/membres
	
### Suppression d'un membre

	$ curl -X DELETE http://0.0.0.0:8888/api/membres/6
