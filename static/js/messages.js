function AfficherGenerique(texte, classe) {
  $.pnotify({
    text: texte,
    type: classe,
    delay: 3000
  });
}

function AfficherSucces(texte) {
  AfficherGenerique(texte, 'success');
}

function AfficherInfo(texte) {
  AfficherGenerique(texte, 'info');
}

function AfficherErreur(texte) {
  AfficherGenerique(texte, 'error');
}

