pieces = null;

$(document).ready(function() {
	$('#debut').datepicker({language: 'fr'});
	$('#fin').datepicker({language: 'fr'});

	$('#ventes').dataTable({
				'bPaginate': false,
});

	$('#afficher').click(function() {
		var debut = $('#debut').val();
		var fin = $('#fin').val();
		var first = true;

		var url = "/api/factures?";

		var params = [];

		if (debut) {
			params.push("debut=" + debut);
		}

		if (fin) {
			params.push("fin=" + fin);
		}

		url += params.join("&");

		/* La première fois qu'on va chercher des ventes, on va d'abord chercher la liste de pièces. */
		if (pieces == null) {
			$.get("/api/pieces").done(function (data, textStatus, jqXHR) {
				liste_pieces = data;
				pieces = {};
				for (k in liste_pieces) {
					piece = liste_pieces[k];
					pieces[piece.numero] = piece;
				}

				$.get(url).done(RemplirTableauVentes).fail(DisplayError);
			}).fail(DisplayError);
		} else {
			$.get(url).done(RemplirTableauVentes).fail(DisplayError);
		}



		return false;
	});
});

function RemplirTableauVentes(data, textStatus, jqXHR) {
	var rows = [];
	var quantites = {};

	// Calculer la quantité par pièce
	for (i in data) {
		var facture = data[i];
		for (j in facture.pieces) {
			var achat = facture.pieces[j];

			if (!(achat.numero in quantites)) {
				quantites[achat.numero] = 0;
			}

			quantites[achat.numero] += achat.quantite;
		}
	}

	// Générer les lignes du tableau
	for (numero in quantites) {
		var piece = pieces[numero];
		var numerobabac = 'numerobabac' in piece ? piece.numerobabac : "";
		var section = piece.section;
		var nom = piece.nom;
		var reference = 'reference' in piece ? piece.reference : "";
		var caracteristique = piece.caracteristique;

		var row = [numero, numerobabac, section, nom, reference, caracteristique, Math.round(quantites[numero])];
		rows.push(row);
	}

	$('#ventes').dataTable().fnClearTable();
	$('#ventes').dataTable().fnAddData(rows);

}
