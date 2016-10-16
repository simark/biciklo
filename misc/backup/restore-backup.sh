#!/usr/bin/env bash

if [ $# -ne 1 ]; then
	echo "Usage: $0 path/to/backup.tar.xz"
	exit 1
fi

echo "ATTENTION! Cette action va écraser le contenu de la base de données \"biciklo\"!"
echo

read -p "Voulez-vous vraiment continuer? Si oui, écrivez \"oui\": " -r
if [ "$REPLY" = "oui" ]
then
	set -e
	set -x

	tmpdir=$(mktemp -d)
	pushd "$tmpdir"
	cp "$1" .
	name=$(basename "$1")
	tar -xf "$name"
	name="${name%%.*}"

	mongo --eval "db.dropDatabase()" biciklo

	mongorestore "$name"
fi
