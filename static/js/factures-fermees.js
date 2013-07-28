
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
  });
}

function ReouvrirFacture() {
  var tr = $(this).closest('tr');
  numeroFacture = tr.attr('data-numero-facture');
  var data = {'complete': 'non'};
  $.ajax({
      'url': '/api/factures/' + numeroFacture,
      'type': 'PUT',
      'data': data,
    }).done(function (data, textStatus, jqXHR) {
      AfficherSucces('Facture réouverte');
      $('#factures-fermees').dataTable().fnDeleteRow(tr.get(0));
    }).fail(DisplayError);
}


$(document).ready(function() {
  InitTableauFacturesFermees();

  $('.reouvrir-facture').click(ReouvrirFacture);
});
