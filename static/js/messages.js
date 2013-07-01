function AfficherGenerique(texte, classe) {
  conteneur = $('#conteneur-messages');

  conteneur.show();

  enfant = $('<div class="alert ' + classe + '"></div>');
  enfant.css('display', 'none');
  enfant.text(texte);

  conteneur.append(enfant);

  enfant.slideDown();

  window.setTimeout(EnleverPremierMessage, 5000);
}

function AfficherSucces(texte) {
  AfficherGenerique(texte, 'alert-success');
}

function AfficherInfo(texte) {
  AfficherGenerique(texte, '');
}

function AfficherErreur(texte) {
  AfficherGenerique(texte, 'alert-error');
}

function EnleverPremierMessage() {
  conteneur = $('#conteneur-messages');
  conteneur.children(':not(:animated)').first().slideUp('normal', function () {
    $(this).remove();

    if (conteneur.children().length == 0) {
      conteneur.hide();
    }
  });
}
