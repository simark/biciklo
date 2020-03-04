#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import yaml


def lire_config():

    fichier_config = Path.home() / '.config' / 'biciklo' / 'config.yml'

    if fichier_config.is_file():

        with fichier_config.open(mode='r') as fichier:
            info_config = yaml.safe_load(fichier)

        utilisateur_babac = info_config['Cycle Babac']['nom utilisateur']
        motdepasse_babac = info_config['Cycle Babac']['mot de passe']


    else:
        with fichier_config.open(mode='w') as fichier:
            yaml.dump({'Cycle Babac': {'nom utilisateur': 'BoblEponge', 'mot de passe': 'BasdeBikini'}}, fichier)

        utilisateur_babac = None
        motdepasse_babac = None

    return utilisateur_babac, motdepasse_babac
