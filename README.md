biciklo
=======

Système d'inventaire pour l'atelier **Biciklo**.

dépendances
-----------
* Python 2 ou 3
  * virtualenv
* MongoDB
* [Compass](http://compass-style.org/)
  * Installer `ruby`, puis `gem install compass`
  * seulement nécessaire pour regénérer les fichiers css.

installation pour le développement
----------------------------------

1. Cloner l'entrepôt

        $ git clone https://github.com/simark/biciklo.git

2. Créer un environnement Python (virtualenv) et l'activer:

        $ virtualenv -p python3 biciklo-env
        $ source biciklo-env/bin/activate

3. Installer le module biciklo

        $ cd biciklo
        $ pip install -e .

4. Lancer l'inventaire:

        $ BICIKLO_DEBUG=1 biciklo-inventaire

Il est alors possible d'accéder à l'inventaire en utilisant l'adresse
affichée par la commande précédente, typiquement [`http://127.0.0.1:8888`](http://127.0.0.1:8888).

Si des modifications sont faites aux fichiers .sass, les fichiers .css
doivent être regénérés:

	$ cd sass
	$ compass compile

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
