
function InitTableauFacturesFermees() {
  // Initialiser le tableau datatables.
  $('#factures-fermees').dataTable({
    'aaData': null,
    'bLengthChange': false,
    'iDisplayLength': 20,
    'oLanguage': {
       sLengthMenu: "afficher _MENU_ entrées par page",
       sZeroRecords: "désolé, aucun résultat trouvé...",
       sInfo: "_START_ à _END_ de _TOTAL_ entrées",
       sInfoEmpty: "0 à 0 d'aucune entrée",
       sInfoFiltered: "(filtré de _MAX_ entrées en tout)",
       sSearch: "rechercher&nbsp;:",
     },
     'fnCreatedRow': function( nRow, aData, iDisplayIndex ) {
       var colonnePrix = 3;
       var colonneReouvrir = 4;

       // Appliquer NombreVersPrix sur la colonne du montant total
       $('td:eq(' + colonnePrix + ')', nRow).html( NombreVersPrix(aData[colonnePrix]) );

       // Mettre le handler du clic sur le bouton pour réouvrir les factures
       $(nRow).find('.reouvrir-facture').click(ReouvrirFacture);

       return nRow;
		},
  });
}

function ReouvrirFacture() {
  var tr = $(this).closest('tr');
  var numeroFacture = tr.attr('data-numero-facture');
  var data = {'complete': 'non'};
  $.ajax({
      'url': '/api/factures/' + numeroFacture,
      'type': 'PUT',
      'data': data,
    }).done(function (data, textStatus, jqXHR) {
      AfficherSucces('Facture #' + numeroFacture + ' réouverte');
      $('#factures-fermees').dataTable().fnDeleteRow(tr.get(0));
    }).fail(DisplayError);
}


$(document).ready(function() {
  InitTableauFacturesFermees();
});
