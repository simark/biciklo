var cache_categories = null;

function Sauvegarder() {
  donnees = {};

  $('#detailspiece input').each(function () {
    var key = $(this).attr('id');
    var val;
    if ($(this).attr('type') == 'checkbox') {
      val = $(this).is(':checked') ? 'oui' : 'non';
    } else {
      val = $(this).val();
    }

    donnees[key] = val;
  });

  numero = $('#numero').text().trim();

  $.ajax({
    url: '/api/pieces/' + numero,
    type: 'PUT',
    dataType: 'json',
    data: donnees,
    }).done(function (data, textStatus, jqXHR) {
      AfficherSucces('Sauvegardé !');
    }).fail(DisplayError);
}

function InitChampCategorie() {
  var champ = $('#section');

  champ.typeahead({
    source: function (query, process) {
      if (cache_categories != null) {
        process(cache_categories);
        return;
      }

      $.get('/api/categoriespieces').done(function( data ) {
        cache_categories = data;
        process(cache_categories);
      });
    }
  });
}

$(document).ready(function() {
  $('#sauvegarder').click(Sauvegarder);

  InitChampCategorie()
});
