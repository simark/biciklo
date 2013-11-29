function RaccourcisClavierModeNormal() {
  SupprimerRaccourcisClavier();

  $(document).keypress(function (event) {
    if (event.which == 109) { // 'm'
      event.preventDefault();
      ModeModification();
    }
  });
}

function RaccourcisClavierModeModification() {
  SupprimerRaccourcisClavier();

  $(document).keydown(function (event) {
    if (event.which == 27) { // echap
      event.preventDefault();
      Annuler();
    } else if (event.which == 13) {
      event.preventDefault();
      Sauvegarder();
    }
  });
}

function ModeModification() {
  $('#annuler').show();
  $('#sauvegarder').show();
  $('#modifier').hide();

  RaccourcisClavierModeModification();

  NormalVersEdition();
}

function ModeNormal(sauvegarder) {
  $('#annuler').hide();
  $('#sauvegarder').hide();
  $('#modifier').show();

  RaccourcisClavierModeNormal();

  EditionVersNormal(sauvegarder);
}

function NormalVersEdition() {
  $('#detailsmembre td[data-edit="text"]').each(function (index, cellule) {
    fixe = $(cellule).find('span');
    champ = $(cellule).find('input[type="text"]');

    champ.val(fixe.text());

    champ.show();
    fixe.hide();
  });

  $('#detailsmembre td[data-edit="radio"]').each(function (index, cellule) {
    fixe = $(cellule).find('span');
    champs = $(cellule).find('input[type="radio"]');
    labels = $(cellule).find('label');

    for (i = 0; i < champs.length; i++) {
      champ = champs[i];
      if ($(champ).val() == fixe.text()) {
        $(champ).click();
      }
    }

    labels.show();
    champs.show();
    fixe.hide();
  });
}

function EditionVersNormal(sauvegarder) {
  $('#detailsmembre td[data-edit="text"]').each(function (index, cellule) {
    fixe = $(cellule).find('span');
    champ = $(cellule).find('input[type="text"]');

    if (sauvegarder) {
      fixe.text(champ.val());
    }

    champ.hide();
    fixe.show();
  });

  $('#detailsmembre td[data-edit="radio"]').each(function (index, cellule) {
    fixe = $(cellule).find('span');
    champs = $(cellule).find('input[type="radio"]');
    labels = $(cellule).find('label');

    if (sauvegarder) {
      fixe.text(champs.filter(':checked').val());
    }

    labels.hide();
    champs.hide();
    fixe.show();
  });
}

function Sauvegarder() {
  donnees = {
    'prenom': $('#prenom input').val(),
    'nom': $('#nom input').val(),
    'listedenvoi': $('#listedenvoi input:checked').val(),
    'courriel': $('#courriel input').val(),
    'provenance': $('#provenance input').val(),
    'estbenevole': $('#estbenevole input:checked').val(),
    'notes': $('#notes input').val(),
  };

  numero = $('#numero').text().trim();

  $.ajax({
    url: '/api/membres/' + numero,
    type: 'PUT',
    dataType: 'json',
    data: donnees,
    }).done(function (data, textStatus, jqXHR) {
      ModeNormal(true);
      AfficherSucces('Sauvegardé !');
    }).fail(DisplayError);
}

function Annuler() {
  $('#annuler').hide();
  $('#sauvegarder').hide();
  $('#modifier').show();

  ModeNormal(false);
}

function Modifier() {
  ModeModification();
}

$(document).ready(function() {
  $('#modifier').click(Modifier);
  $('#sauvegarder').click(Sauvegarder);
  $('#annuler').click(Annuler);

  RaccourcisClavierModeNormal();
});
