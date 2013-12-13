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
    var postData = {'numero': numeroPiece, 'fusionsiexiste': "oui", 'quantite': quantite};

    $.post(postUrl, postData).done(function (ligneFacture, textStatus, jqXHR) {
        SupprimerLignePiece(numeroFacture, numeroPiece);
        AjouterLignePiece(numeroFacture, piece, ligneFacture);

        champNumeroPiece.val("");
        champQuantite.val("");

        CalculerPrixTotalFacture(numeroFacture);

        AfficherSucces("Fait !");

        $.get("/api/membres/" + $('#facture-' + numeroFacture).attr('data-numero-membre')).done(function (membre) {
          VerifierAbonnement(membre, numeroFacture);
        }).fail(DisplayError);

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
      InstallerTypeaheadPieces();
      AfficherSucces("Facture ajoutée");

      $('#input-nouvelle-facture').val("");
    }).fail(DisplayError);
  return false;
}

function ChargerFacture(facture) {
  // Cloner le template
  var template = $('#facture-template');
  var divfacture = template.clone();

  divfacture.attr('id', 'facture-' + facture.numero);
  divfacture.attr('data-numero-facture', facture.numero);
  divfacture.attr('data-numero-membre', facture.membre);
  divfacture.find('.form-ajout-piece-facture').submit(SubmitAjoutPiece);

  divfacture.appendTo( $('#factures-container') );
  divfacture.find('.remove').click(SupprimerFacture);
  divfacture.find('.close').click(FermerFacture);

  // Requête membre
  var httpRequests = [];
  httpRequests.push($.get('/api/membres/' + facture.membre));

  if (facture.pieces) {
    // Requête pièces
    $.each(facture.pieces, function (k, ligneFacture) {
      httpRequests.push($.get('/api/pieces/' + ligneFacture.numero));
    });
  }

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
    divfacture.find('.titre').html('<a href="/membres/' + membre.numero + '">' + nom + "</a> - membre #" + membre.numero + " - facture #" + facture.numero + " - " + FormatDate(facture.date));

    VerifierAbonnement(membre, facture.numero);

  }).fail(DisplayError);
}

function VerifierAbonnement(membre, numeroFacture) {
  var divfacture = $('#facture-' + numeroFacture);

  divfacture.find('.titre').removeClass('abonnement-expire');
  divfacture.find('.titre').removeClass('abonnement-absent');

  if (membre.expiration && membre.expiration['$date']) {
    exp = new Date(membre.expiration['$date']);
    now = new Date();
    if (exp < now) {
      divfacture.find('.titre').addClass('abonnement-expire');
    }
  } else {
    divfacture.find('.titre').addClass('abonnement-absent');
  }
}

function AjouterLignePiece(numeroFacture, piece, ligneFacture) {
  function GetProp(obj, prop, alt) {
    alt = typeof alt !== 'undefined' ? alt : '?';
    return (prop in obj) ? obj[prop] : alt;
  }

  html = $('<tr class="ligne-facture"></tr>');
  html.attr('data-prixtotal', ligneFacture.prixtotal);
  html.attr('data-numero-piece', piece.numero);

  numero = GetProp(piece, "numero");

  html.append(Mustache.render('<td><a href="/pieces#{{numero}}">{{numero}}</a></td>', {numero: numero}));
  html.append('<td>' + GetProp(piece, "section") + '</td>');
  html.append('<td>' + GetProp(piece, "nom") + '</td>');
  html.append('<td>' + GetProp(piece, "reference") + '</td>');

  html.append('<td>' + GetProp(ligneFacture, 'quantite', '') + '</td>');
  html.append('<td>' + NombreVersPrix(GetProp(ligneFacture, 'prix', '')) + '</td>');

  html.append('<td>' + NombreVersPrix(ligneFacture.prixtotal) + '</td>');

  html.append('<td><i class="icon icon-remove"></i></td>');
  html.find("i").click(SupprimerPiece);

  divfacture = $('#facture-' + numeroFacture);
  divfacture.find('.contenu table tbody tr').last().before(html);
}

function SupprimerLignePiece(numeroFacture, numeroPiece) {
	$('#facture-' + numeroFacture).find('tr[data-numero-piece=' + numeroPiece + ']').remove();
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
      $('#facture-' + numeroFacture).slideUp('slow', function () { $(this).remove(); });
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
      $('#facture-' + numeroFacture).slideUp('slow', function () { $(this).remove(); });
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
    SupprimerLignePiece(numeroFacture, numeroPiece);
    CalculerPrixTotalFacture(numeroFacture);

    $.get("/api/membres/" + $('#facture-' + numeroFacture).attr('data-numero-membre')).done(function (membre) {
          VerifierAbonnement(membre, numeroFacture);
    }).fail(DisplayError);

  }).fail(DisplayError);
}

function CalculerPrixTotalFacture(numeroFacture) {
  facture = $('#facture-' + numeroFacture);
  var prixtotal = 0; //en cents

  $.each(facture.find('table').find('tr[data-prixtotal]'), function (k, row) {
    prixtotal += parseInt($(row).attr('data-prixtotal'));
  });

  prixtotal = Math.round(prixtotal/25)*25; //arrondi au 25 cent le plus pres

  facture.find('.total').html("Total: " + NombreVersPrix(prixtotal));
}

function InstallerTypeaheadPieces() {
  $('.input-numero-piece').removeData('typeahead');
  $('.input-numero-piece').unbind();
  $('.input-numero-piece').typeahead({
    source: listePieces,
    updater: parseInt, // Ça ne retient que le nombre du début
  });
}

$(document).ready(function () {
  // Batir liste de pieces pour autocomplete
  $.get('/api/pieces', null, function (data, textStatus, jqXHR) {
    listePieces = []

    $.each(data, function(key, piece) {
      s = piece.numero.toString() + " - "
        + piece.section + " - "
        + piece.nom + " - "
        + piece.reference + " ("
        + NombreVersPrix(piece.prix) + ")" ;
      listePieces.push(s);
    });

    InstallerTypeaheadPieces();
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
  $.get('/api/factures?complete=non', {})
    .done(function (data, textStatus, jqXHR) {
      $.each(data, function(key, facture) {
        ChargerFacture(facture);
      });

      InstallerTypeaheadPieces();

      $('#loading').hide();
    }).fail(DisplayError);
});
