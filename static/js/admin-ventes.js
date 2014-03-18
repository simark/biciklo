$(document).ready(function() {
	$('#debut').datepicker({language: 'fr'});
	$('#fin').datepicker({language: 'fr'});

	$('#ventes').dataTable({
				'aaData': [],
				'bPaginate': false,
				'aoColumns': [
						{
							sTitle: '#',
						},
						{
							sTitle: 'quantité',
						},
				],
			});

	$('#afficher').click(function() {
		var debut = $('#debut').val();
		var fin = $('#fin').val();
		var first = true;

		var url = "/api/factures?";

		if (debut) {
			if (!first) {
				url += "&";
			}

			url += "debut=" + debut;
			first = false;
		}

		if (fin) {
			if (!first) {
				url += "&";
			}

			url += "fin=" + fin;
			first = false;
		}

		$.get(url).done(function (data, textStatus, jqXHR) {
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
				var row = [numero, quantites[numero]];
				rows.push(row);
			}

			$('#ventes').dataTable().fnClearTable();
			$('#ventes').dataTable().fnAddData(rows);

		}).fail(DisplayError);

		return false;
	});
});
