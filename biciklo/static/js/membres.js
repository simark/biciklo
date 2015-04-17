/**
 * Lis et retourne les champs du formulaire d'inscription d'un membre.
 *
 * @return Objet possédant les clés/valeurs à envoyer au serveur.
 */
function LireChampsAjoutMembre() {
  var request_data = {};

  request_data.prenom = $('#ajoutprenom').val();
  request_data.nom = $('#ajoutnom').val();
  request_data.courriel = $('#ajoutcourriel').val();
  request_data.provenance = $('#ajoutprovenance').val();
  request_data.listedenvoi = ($('#ajoutlistedenvoi').prop('checked')) ? 'oui' : 'non';
  request_data.notes = $('#ajoutnotes').val();

  return request_data;
}

/**
 * Envoie une requête d'ajout d'un membre au serveur.
 */
function EnvoyerAjoutMembre() {
  donneesRequete = LireChampsAjoutMembre();

  // Envoyer la requête au serveur.
  $.ajax({
    url: '/api/membres',
    type: 'POST',
    data: donneesRequete,
    dataType: 'json',
  }).done(function (data, textStatus, jqXHR) {
    // Fermer le dialogue et réinitialiser le formulaire.
    $('#ajoutmembre').modal('hide');

    // Afficher une confirmation.
    AfficherInfo('Membre ' + donneesRequete.prenom + ' ' + donneesRequete.nom + ' (#' + data['numero'] + ') ajouté.');

    // Recharger la liste de membres.
    RechargerListeMembres();
  }).fail(DisplayError);
}

/**
 * Initialise le formattage du tableau de membres.
 */
function InitListeMembres() {
  // Initialiser le tableau datatables.
  $('#membres').dataTable({
    'aaData': null,
    'bLengthChange': false,
    'iDisplayLength': 20,
    'oLanguage': {
       sLengthMenu: "afficher _MENU_ entrées par page",
       sZeroRecords: "désolé, aucun résultat trouvé...",
       sInfo: "_START_ à _END_ de _TOTAL_ entrées",
       sInfoEmpty: "0 à 0 d'aucune entrée",
       sInfoFiltered: "(filtré de _MAX_ entrées en tout)",
       sSearch: "rechercher&nbsp;:",
     },
     // Lorsqu'une ligne est crée, on ajoute un click handler.
     'fnCreatedRow': function (nRow, aData, iDataIndex) {
        $(nRow).click(function() {
          // Le numero du membre est dans la premiere cellule de la ligne.
          numero = aData[0];
          location.href = ('/membres/' + numero);
        });
     },
  });
}

/**
 * Remplis la liste des membres à partir de la liste JSON reçue du serveur.
 */
function RemplirTableauMembres(membres_json) {
  tableau = $('#membres');

  RemplirTableauGenerique(membres_json, tableau);

  // Afficher le tableau, cacher l'indicateur de chargement.
  $('#loading').hide();
  $('#membres').show();
  $('#membres_wrapper').show();
}

/**
 * Charge la liste de membres et remplit le tableau.
 */
function RechargerListeMembres() {
  // Cacher le tableau, afficher l'indicateur de chargement.
  $('#membres').hide();
  $('#membres_wrapper').hide();
  $('#loading').show();

  // Faire la requête au serveur.
  $.ajax({
    url: '/api/membres',
    dataType: 'json',
  }).done(function(data, textStatus, jqXHR) {
    RemplirTableauMembres(data);
  }).fail(DisplayError);
}

/**
 * Effectue la transition vers le mode normal.
 */
function RaccourcisClavierModeNormal() {
  SupprimerRaccourcisClavier();

  $(document).keypress(function (event) {
    if (event.keyCode == 43) { // '+'
      event.preventDefault();
      ModeAjout();
    } else if (event.keyCode == 47) { // '/'
      event.preventDefault();
      $('#membres_filter input').focus();
    }
  });
}

/**
 * Effectue la transition vers le mode ajout d'un membre.
 */
function RaccourcisClavierModeAjout() {
  SupprimerRaccourcisClavier();

  $(document).keyup(function (event) {
    if (event.keyCode == 27) { // escape
      event.preventDefault();
      ModeNormal();
    }
  });
}

function ModeAjout() {
  $('#ajoutmembre').modal('show');
}

function ModeNormal() {
  $('#ajoutmembre').modal('hide');
}

/**
 * Initialise ce qui est en lien avec le formulaire d'ajout d'un membre.
 */
function InitFormulaireAjoutMembre() {
  // Champ provenance
  $('#ajoutprovenance').typeahead({
    source: ObtenirChoixProvenance,
    minLength: 0,
    delay: 0,
  });
  $("#ajoutprovenance").focus($("#ajoutprovenance").typeahead.bind($("#ajoutprovenance"), 'lookup'));

  // Champ remarques
  $('#ajoutnotes').typeahead({
    source: ["Bouche à oreille", "Affiche", "Ma santé au sommet", "Site web"],
    minLength: 0,
    delay: 0,
  });
  $("#ajoutnotes").focus($("#ajoutnotes").typeahead.bind($("#ajoutnotes"), 'lookup'));

  // Bouton submit
  $('#ajoutenvoyer').click(function (event) {
    EnvoyerAjoutMembre();
  });

  $('#ajoutmembre').on('hide', function() {
    RaccourcisClavierModeNormal();
    ReinitialiserFormulaireAjoutMembre();
  });

  $('#ajoutmembre').on('show', function() {
    RaccourcisClavierModeAjout();
  });

  $('#ajoutmembre').on('shown', function() {
    $('#ajoutmembre').find('input').first().focus();
  });
}

/**
 * Réinitialise les champs du formulaire.
 */
function ReinitialiserFormulaireAjoutMembre() {
  $('#ajoutprenom').val("");
  $('#ajoutnom').val("");
  $('#ajoutcourriel').val("");
  $('#ajoutprovenance').val("");
  $('#ajoutnotes').val("");
  $('#ajoutlistedenvoi').prop('checked', false);
}

$(document).ready(function () {
  InitCommun();

  InitFormulaireAjoutMembre();

  InitListeMembres();
  RechargerListeMembres();

  RaccourcisClavierModeNormal();
});
