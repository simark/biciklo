
function InitTableauPieces() {
  // Initialiser le tableau datatables.
  $('#pieces').dataTable({
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

function RemplirTableauPieces(liste_pieces) {
  tableau = $('#pieces');

  RemplirTableauGenerique(liste_pieces, tableau);

  // Afficher le tableau, cacher l'indicateur de chargement.
  $('#loading').hide();
  $('#pieces').show();
  $('#pieces_wrapper').show();
}

/**
 * Charge la liste de membres et remplit le tableau.
 */
function RechargerTableauPieces() {
  $('#pieces').hide();
  $('#pieces_wrapper').hide();
  $('#loading').show();

  $.ajax({
    url: '/api/pieces',
    dataType: 'json',
  }).done(function(data, textStatus, jqXHR) {
    RemplirTableauPieces(data);
  }).fail(function(jqXHR, textStatus, errorThrown) {
    AfficherErreur('Erreur lors du téléchargement de la liste de membres: ' + errorThrown);
  });
}

$(document).ready(function() {
  InitTableauPieces();
  RechargerTableauPieces();
});
