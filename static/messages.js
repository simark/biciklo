function AfficherInfo(texte) {
  conteneur = $('#conteneur-messages');

  conteneur.show();

  enfant = $('<div class="ui-state-highlight ui-corner-all"></div>');
  enfant.css('display', 'none');
  enfant.text(texte);

  conteneur.append(enfant);
  
  enfant.slideDown();

  window.setTimeout(EnleverPremierMessage, 2000);
}

function AfficherErreur(texte) {
  conteneur = $('#conteneur-messages');

  conteneur.show();

  enfant = $('<div class="ui-state-error ui-corner-all"></div>');
  enfant.text(texte);

  conteneur.append(enfant);

  window.setTimeout(EnleverPremierMessage, 6000);
}

function EnleverPremierMessage() {
  console.log("EPM called");
  conteneur = $('#conteneur-messages');
  conteneur.children(':not(:animated)').first().slideUp('normal', function () {
    $(this).remove();

    if (conteneur.children().length == 0) {
      conteneur.hide();
    }
  });
}
