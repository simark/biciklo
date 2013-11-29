function Sauvegarder() {
  donnees = {};

  $('#detailspiece input').each(function () {
    var val = $(this).val();
    var key = $(this).attr('id');

    if (val.length > 0) {
      donnees[key] = val;
    }
  });

  numero = $('#numero').text().trim();

  $.ajax({
    url: '/api/pieces/' + numero,
    type: 'PUT',
    dataType: 'json',
    data: donnees,
    }).done(function (data, textStatus, jqXHR) {
      AfficherSucces('Sauvegardé !');
    }).fail(function (jqXHR, textStatus, errorThrown) {
      AfficherErreur('Erreur lors de la sauvegarde: ' + errorThrown);
  });
}

$(document).ready(function() {
  $('#sauvegarder').click(Sauvegarder);
});
