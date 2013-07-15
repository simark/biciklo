var listePieces = null;

function DisplayError(jqXHR, textStatus, errorThrown) {
  data = jqXHR.responseText;
  AfficherErreur(JSON.parse(data));
}

function AjouterFacture(numeroFacture, numeroMembre) {
  $.get('/api/membres/' + numeroMembre, {}, function(data, textStatus, jqXHR) {
    nom = data.prenom + " " + data.nom;

    template = $('#commande-template');
    divCommande = template.clone();

    divCommande.attr('id', 'commande-' + numeroFacture);
    titre = nom + " (facture " + numeroFacture + ")";
    divCommande.find('.commande-titre').first().text(titre);

    divCommande.find('.input-numero-piece').typeahead({
      source: listePieces,
      updater: parseInt, // Ça ne retient que le nombre du début
    });

    divCommande.find('.form-ajout-piece-facture').submit(function () {
      numeroPiece = $(this).find('.input-numero-piece').val();
      quantite = $(this).find('.input-quantite-piece').val();
      numeroFacture = $(this).closest('.commande-container').attr('id').replace('commande-', '');

      if (numeroPiece.length == 0) {
        AfficherErreur("Il faut un numéro de pièce.");
        return false;
      }

      if (quantite.length == 0) {
        AfficherErreur("Il faut une quantité.");
        return false;
      }

      $.post('/api/factures/' + numeroFacture + '/pieces',
        {numero: numeroPiece, quantiteneuf: quantite})
        .done(function (data, textStatus, jqXHR) {
          console.log(data);
        })
        .fail(DisplayError);

      return false;
    });

    divCommande.appendTo( $('#commandes-container') );
  })
    .fail(DisplayError);

}



$(document).ready(function () {
  // Batir liste de pieces
  $.get('/api/pieces', null, function (data, textStatus, jqXHR) {
    listePieces = []

    $.each(data, function(key, piece) {
      s = piece.numero.toString() + " - " + piece.nom;
      listePieces.push(s);
    });
  });

  // Batir liste de membres
  $.get('/api/membres', null, function (data, textStatus, jqXHR) {
    listeMembres = []

    $.each(data, function(key, membre) {
      s = membre.numero.toString() + " - " + membre.prenom + " " + membre.nom;
      listeMembres.push(s);
    });

    $('#input-nouvelle-commande').typeahead({
      source: listeMembres,
      updater: parseInt,
    });
  });

  // Action ajouter nouvelle commande
  $('#form-nouvelle-commande').submit(function () {
    numeroMembre = $('#input-nouvelle-commande').val();
    if (numeroMembre.length == 0) {
      AfficherErreur("Il manque le numéro de membre.");
      return false;
    }

    $.post('/api/factures', {'membre': numeroMembre})
      .done(function (data, textStatus, jqXHR) {
        AjouterFacture(data.numero, numeroMembre);
      })
      .fail(DisplayError);
    return false;
  });

  // Aller chercher les commandes existantes
  $.get('/api/factures', {})
    .done(function (data, textStatus, jqXHR) {
      $.each(data, function(key, facture) {
        AjouterFacture(facture.numero, facture.membre);
      });
    })
    .fail(DisplayError);
});
