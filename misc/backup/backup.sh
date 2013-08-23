#!/bin/bash

# Nom de la base de donnée à sauvegarder
dbname="biciklo"

# Dossier où placer l'archive
destination="/tmp"

# Nom de base de l'archive (.tar.xz sera ajouté)
name=$(date "+biciklo_%Y%m%d_%H%M%S")

# Dossier temporaire
tmpdir="/tmp"

mongodump --db "$dbname" --out "$tmpdir/$name"
tar -cvJf "$destination/$name.tar.xz" -C "$tmpdir" "$name"


