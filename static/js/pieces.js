var showPiecesInactives = false;

function AfficherAjouterPieceAFacture(numeroPiece) {
  $.get("/api/factures?complete=non").done(function (factures, textStatus, jqXHR) {
    if (factures.length == 0) {
      AfficherInfo("Il n'y a aucune facture ouverte.");
      return;
    }

    var gets = [];

    $.each(factures, function (k, facture) {
      gets.push($.get('/api/membres/' + facture.membre));
    });

    $.when.apply($, gets).done(function () {
      var html = "";
      var membres;

      if (gets.length > 1) {
        membres = $.map(arguments, function (e) { return e[0]; });
      } else if (gets.length == 1) {
        membres = [arguments[0]];
      }

      for (var i = 0; i < gets.length; i++) {
        facture = factures[i];
        membre = membres[i];

        html += "<button type=\"button\" class=\"btn\" data-numerofacture=\"" + facture.numero + "\">" + facture.numero + " - " + membre.prenom + " " + membre.nom + "</button><br>"
      }

      var modal = $('#ajout-a-facture');

      modal.find('h3').text(Mustache.render("Pièce #{{numero}}", {numero: numeroPiece }));
      modal.find('#boutons-factures').html(html);
      modal.find('input[type=text]').val("");
      modal.attr('data-numeropiece', numeroPiece);
      modal.modal("show");

    }).fail(DisplayError);
  }).fail(DisplayError);
}

function SubmitAjouterPiece() {
  var quantite = $('#quantite').val();
  var numeroPiece = $('#ajout-a-facture').attr('data-numeropiece');
  var checkedBtn = $('#ajout-a-facture #boutons-factures button.active');

  if (checkedBtn.length != 1) {
    AfficherErreur("Il faut choisir une facture");
    return false;
  }

  if (quantite.length == 0) {
    AfficherErreur("Il faut au moins une quantité");
    return false;
  }

  var numeroFacture = checkedBtn.attr('data-numerofacture');
  var params = {'numero': numeroPiece, 'fusionsiexiste': 'oui', 'quantite': quantite};

  $.post('/api/factures/' + numeroFacture + '/pieces', params).done(function() {
    AfficherSucces("Fait!");
    $('#ajout-a-facture').modal('hide');
  }).fail(DisplayError);

  return false;
}

function ListePiecesColonneIconesData() {
  return '<i style="display: inline-block;" class="icon icon-plus icone-ajouter-a-facture"></i>' +
         '&nbsp;' +
         '<a href="#"><i class="icon icon-edit icone-modifier-piece"></i></a>';
}

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
       sSearch: "rechercher dans toutes les colonnes:",
     },
    'fnCreatedRow': function (nRow, aData, iDataIndex) {
        // Le numero du membre est dans la premiere cellule de la ligne.
        numero = aData[0];
        $(nRow).find('i.icone-ajouter-a-facture').click(AfficherAjouterPieceAFacture.bind(undefined, numero));
        $(nRow).find('i.icone-modifier-piece').parent().attr('href', '/pieces/' + numero);
     },
     'aoColumnDefs': [
       {
         'aTargets': [-1],
         'sClass': 'liste-pieces-cellule-colonne-icones',
       },
     ]
  });

  $.fn.dataTableExt.afnFiltering.push(function (oSettings, aData, iDataIndex) {
    if (showPiecesInactives) {
      return true;
    }

    return ! $(oSettings.aoData[iDataIndex].nTr).hasClass("inactive");
  });
}

function RemplirTableauPieces(liste_pieces) {
  var tableau = $('#pieces');

  RemplirTableauGenerique(liste_pieces, tableau);

  // Afficher le tableau, cacher l'indicateur de chargement.
  $('#loading').hide();
  $('#pieces').show();
  $('#pieces_wrapper').show();
}

function ListePiecesRowClass(ligne_data) {
  if ('active' in ligne_data && ligne_data.active == false) {
    return "inactive";
  }
}

/**
 * Charge la liste de pièces et remplit le tableau.
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
    InitialiserFiltres();

  }).fail(DisplayError);
}

function InitialiserFiltres() {
  $('#pieces').dataTable().columnFilter({
    sPlaceHolder: "head:after",
    aoColumns: [
      {type: 'number', sSelector: '#filtre-numero'},
      {type: 'select', sSelector: '#filtre-section'},
      {sSelector: '#filtre-nom'},
      {sSelector: '#filtre-reference'},
    ]
  });

  $('#filtre-numero input').addClass('input-mini');
  $('#filtre-nom input').addClass('input-small');

  $('#pieces-actives-seulement').change(function() {
    showPiecesInactives = ! $(this).is(":checked");
    $('#pieces').dataTable().fnDraw();
  });

  if (window.location.hash) {
    hash = window.location.hash.substring(1);
    $('#filtre-numero input').val(hash).keyup();
  }
}

function InitFormulaireAjoutPiece() {
  // Bouton submit
  $('#ajoutenvoyer').click(function (event) {
    EnvoyerAjoutPiece();
  });

  $('#ajoutpiece').on('hide', function() {
    $('#ajoutnumero').val("");
  });

  $('#ajoutpiece').on('shown', function() {
    $('#ajoutpiece').find('input').first().focus();
  });
}

function EnvoyerAjoutPiece() {
  numero = $('#ajoutnumero').val();

  if (numero.length == 0) {
    AfficherErreur("Il manque le numéro");
    return;
  }

  // Envoyer la requête au serveur.
  $.ajax({
    url: '/api/pieces',
    type: 'POST',
    data: {numero: numero, active: "oui"},
    dataType: 'json',
  }).done(function (data, textStatus, jqXHR) {
    // Fermer le dialogue et réinitialiser le formulaire.
    $('#ajoutpiece').modal('hide');

    window.location.href = "/pieces/" + numero;
  }).fail(DisplayError);
}

$(document).ready(function() {
  InitTableauPieces();
  RechargerTableauPieces();
  InitFormulaireAjoutPiece();

  $('#filtre-reset').click(function () {
    $('#filtre-numero input').val('').keyup();
    $('#filtre-section select').val('').change();
    $('#filtre-nom input').val('').keyup();
    $('#filtre-reference input').val('').keyup();

  });
  $('#form-ajouter-a-facture').submit(SubmitAjouterPiece);
});
