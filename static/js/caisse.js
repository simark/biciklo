var listePieces = null;

function SubmitAjoutPiece() {
  var champNumeroPiece = $(this).find('.input-numero-piece');
  var champQuantite = $(this).find('.input-quantite-piece');

  var numeroPiece = champNumeroPiece.val();
  var quantite = champQuantite.val();
  var numeroFacture = CetteFacture(this);

  if (numeroPiece.length == 0) {
    AfficherErreur("Il faut un numéro de pièce.");
    return false;
  }

  if (quantite.length == 0) {
    AfficherErreur("Il faut une quantité.");
    return false;
  }

  $.get('/api/pieces/' + numeroPiece).done( function(piece) {
    var postUrl = '/api/factures/' + numeroFacture + '/pieces';
    var postData = {numero: numeroPiece, quantiteneuf: quantite};
    $.post(postUrl, postData).done(function (ligneFacture, textStatus, jqXHR) {
        AjouterLignePiece(numeroFacture, piece, ligneFacture);

        champNumeroPiece.val("");
        champQuantite.val("");

        CalculerPrixTotalFacture(numeroFacture);
      }).fail(DisplayError);
  }).fail(DisplayError);

  return false;
}

function SubmitAjoutFacture() {
  numeroMembre = $('#input-nouvelle-facture').val();

  if (numeroMembre.length == 0) {
    AfficherErreur("Il manque le numéro de membre.");
    return false;
  }

  $.post('/api/factures', {'membre': numeroMembre})
    .done(function (facture, textStatus, jqXHR) {
      ChargerFacture(facture);
      AfficherSucces("Facture ajoutée");

      $('#input-nouvelle-facture').val("");
    })
    .fail(DisplayError);
  return false;
}

function ChargerFacture(facture) {
  // Cloner le template
  var template = $('#facture-template');
  var divfacture = template.clone();

  divfacture.attr('id', 'facture-' + facture.numero);
  divfacture.attr('data-numero-facture', facture.numero);
  divfacture.find('.input-numero-piece').typeahead({
    source: listePieces,
    updater: parseInt, // Ça ne retient que le nombre du début
  });
  divfacture.find('.form-ajout-piece-facture').submit(SubmitAjoutPiece);

  divfacture.appendTo( $('#factures-container') );
  divfacture.find('.remove').click(SupprimerFacture);
  divfacture.find('.close').click(FermerFacture);

  // Requête membre
  var httpRequests = [];
  httpRequests.push($.get('/api/membres/' + facture.membre));

  // Requête pièces
  $.each(facture.pieces, function (k, ligneFacture) {
    httpRequests.push($.get('/api/pieces/' + ligneFacture.numero));
  });

  $.when.apply($, httpRequests).done(function() {
    // Lorsque toutes les requêtes HTTP sont terminées avec succès.
    var pieces;
    var membre;

    // Extraire les réponses
    if (httpRequests.length > 1) {
      pieces = $.map(arguments, function (e) { return e[0]; });
      membre = pieces.shift();
    } else {
      pieces = []
      membre = arguments[0];
    }

    // Ajouter les lignes à la facture
    $.each(pieces, function (k, piece) {
      AjouterLignePiece(facture.numero, piece, facture.pieces[k]);
    });

    CalculerPrixTotalFacture(facture.numero);

    // Mettre les infos du membre
    nom = membre.prenom + " " + membre.nom;
    divfacture.find('.titre').text(nom + " (facture " + facture.numero + ")");
  }).fail(function () {
    AfficherErreur(DisplayError);
  });
}

function AjouterLignePiece(numeroFacture, piece, ligneFacture) {
  function GetProp(obj, prop) {
    return (prop in obj) ? obj[prop] : '?';
  }

  html = $('<tr class="ligne-facture"></tr>');
  html.attr('data-prixtotal', ligneFacture.prixneuf * ligneFacture.quantiteneuf);
  html.append('<td>' + GetProp(piece, "numero") + '</td>');
  html.append('<td>' + GetProp(piece, "section") + '</td>');
  html.append('<td>' + GetProp(piece, "nom") + '</td>');
  html.append('<td>' + GetProp(piece, "reference") + '</td>');

  html.append('<td>' + ligneFacture.quantiteneuf + '</td>');
  html.append('<td>' + NombreVersPrix(ligneFacture.prixneuf) + '</td>');
  html.append('<td>' + NombreVersPrix(ligneFacture.prixneuf * ligneFacture.quantiteneuf) + '</td>');
  html.append('<td><i class="icon-remove"></i></td>');

  html.attr('data-numero-piece', piece.numero);
  html.find("i").click(SupprimerPiece);

  divfacture = $('#facture-' + numeroFacture);
  divfacture.find('.contenu table tbody tr').last().before(html);
}

function CetteFacture(zis) {
  return $(zis).closest('.facture-container').attr('data-numero-facture');
}

function CettePiece(zis) {
  return $(zis).closest(".ligne-facture").attr('data-numero-piece');
}

function SupprimerFacture() {
  var numeroFacture = CetteFacture(this);
  ret = confirm("Supprimer la facture " + numeroFacture + "? Cette action est irréversible, fais attention!")
  if (ret) {
    $.ajax({
      'url': '/api/factures/' + numeroFacture,
      'type': 'DELETE'
    }).done(function (data, textStatus, jqXHR) {
      AfficherSucces('Facture supprimée');
      $('#facture-' + numeroFacture).hide('slow', function () { $(this).remove(); });
    }).fail(DisplayError);
  }
}

function FermerFacture() {
  var numeroFacture = CetteFacture(this);
  var data = {'complete': 'oui'};
    $.ajax({
      'url': '/api/factures/' + numeroFacture,
      'type': 'PUT',
      'data': data,
    }).done(function (data, textStatus, jqXHR) {
      AfficherSucces('Facture fermée');
      $('#facture-' + numeroFacture).hide('slow', function () { $(this).remove(); });
    }).fail(DisplayError);
}

function SupprimerPiece() {
  var numeroPiece = CettePiece(this);
  var numeroFacture = CetteFacture(this);

  $.ajax({
    'url': '/api/factures/' + numeroFacture + '/pieces/' + numeroPiece,
    'type': 'DELETE'
  }).done(function (data, textStatus, jqXHR) {
    AfficherSucces('Pièce supprimée');
    $('#facture-' + numeroFacture).find('tr[data-numero-piece=' + numeroPiece + ']').remove();
    CalculerPrixTotalFacture(numeroFacture);
  }).fail(DisplayError);
}

function CalculerPrixTotalFacture(numeroFacture) {
  facture = $('#facture-' + numeroFacture);
  var prixtotal = 0; //en cents

  $.each(facture.find('table').find('tr[data-prixtotal]'), function (k, row) {
    prixtotal += parseInt($(row).attr('data-prixtotal'));
  });

  prixtotal = Math.round(prixtotal/25)*25; //arrondi au 25 cent le plus pres

  facture.find('.total').text("Total: " + NombreVersPrix(prixtotal));
}

$(document).ready(function () {
  // Batir liste de pieces pour autocomplete
  $.get('/api/pieces', null, function (data, textStatus, jqXHR) {
    listePieces = []

    $.each(data, function(key, piece) {
      s = piece.numero.toString() + " - " + piece.nom;
      listePieces.push(s);
    });
  });

  // Batir liste de membres pour autocomplete
  $.get('/api/membres', null, function (data, textStatus, jqXHR) {
    listeMembres = []

    $.each(data, function(key, membre) {
      s = membre.numero.toString() + " - " + membre.prenom + " " + membre.nom;
      listeMembres.push(s);
    });

    $('#input-nouvelle-facture').typeahead({
      source: listeMembres,
      updater: parseInt,
    });
  });

  // Action ajouter nouvelle facture
  $('#form-nouvelle-facture').submit(SubmitAjoutFacture);

  // Aller chercher les factures existantes
  $.get('/api/factures', {})
    .done(function (data, textStatus, jqXHR) {
      $.each(data, function(key, facture) {
        if (!facture['complete']) {
          ChargerFacture(facture);
        }
      });

      $('#loading').hide();
    })
    .fail(DisplayError);
});
