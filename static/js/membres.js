var liste_prenoms_membres = [];

/**
 * Lis les champs du formulaire d'inscription d'un membre et retourne les
 * valeurs à envoyer dans un object/dict.
 */
function LireChampsNouveauMembre() {
  request_data = {};

  request_data.prenom = $('#ajoutprenom').val();
  request_data.nom = $('#ajoutnom').val();
  request_data.courriel = $('#ajoutcourriel').val();
  request_data.provenance = $('#ajoutprovenance').val();
  request_data.listedenvoi = ($('#ajoutlistedenvoi').prop('checked')) ? 'oui' : 'non';
  
  return request_data;
}

/**
 * Envoie une requête d'inscription d'un nouveau membre au serveur.
 */
function EnvoyerNouveauMembre() {
  donnees_requete = LireChampsNouveauMembre();

  // Envoyer la requête au serveur.
  $.ajax({
    url: '/api/membres',
    type: 'POST',
    data: donnees_requete,
    dataType: 'json',
  }).done(function (data) {
    if (data.status == 'ok') {
      // Fermer le dialogue et réinitialiser le formulaire.
      $('#ajoutmembre').dialog('close');
      $('#ajoutreinitialiser').click();

      // Afficher une confirmation.
      AfficherInfo('Membre ' + request_data.prenom + ' ' + request_data.nom + ' (#' + data.numero + ') ajouté.');
      
      // Recharger la liste de membres.
      RechargerListeMembres();
    } else {
      AfficherErreur('Erreur: ' + data.errorstr);
    }
  }).fail(function () {
    AfficherErreur('Erreur lors de la connexion au serveur.');
  });
}


/**
 * Initialise le formattage du tableau de membres.
 */
function InitialiserTableauMembres() {
  // Initialiser le tableau datatables.
  $('#membres').dataTable({
    'aaData': null,
    'bJQueryUI': true,
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

// Considerer utiliser dataTables' mDataProp
function RemplirTableauMembres(membres_json) {
  tableau = $('#membres');
  tableau.dataTable().fnClearTable();
  
  colonnes = []
  membres = new Array();

  // Aller chercher les infos sur les colonnes.
  $('#membres th').each(function(i) {
    
    colonnes.push({
      source: $(this).attr('data-column'),
      transform: $(this).attr('data-transform'),
    });
  });
  
  // Pour constuire la liste de prenoms.
  prenoms_vus = {};

  // Créer une ligne par membre.
  for (i in membres_json) {
    
    membre_json = membres_json[i];

    // Ajouter le prenom a la liste de prenoms vus.
    'prenom' in membre_json && prenoms_vus[membre_json.prenom] = 1;

    membre = new Array();

    // Créer le tableau d'infos pour ce membre.
    for (col in colonnes) {
      colname = colonnes[col].source;
      transform = colonnes[col].transform;

      if (colname in membre_json) {
        valeur = membre_json[colname];

        // Si une fonction de transformation est spécifiée, l'appeler.
        if (transform && transform in window &&
            typeof(window[transform] == "function")) {
          valeur = window[transform](valeur);
        }
        membre.push(valeur);
      } else {
        membre.push('?');
      }
    }

    membres.push(membre);
  }
 
  // Ajouter les rangées au tableau.
  tableau.dataTable().fnAddData(membres);

  // Afficher le tableau, cacher l'indicateur de chargement.
  $('#loading').hide();
  $('#membres').show();
  $('#membres_wrapper').show();

  // Sauver la liste de prénoms.
  liste_prenoms_membres = Object.keys(prenoms_vus).sort();

  // Pour l'autocomplete des prenoms;
  $('#ajoutprenom').autocomplete({
    source: FiltreAutocompletePrenoms,
    minLength: 1,
    delay: 0,
  }).focus(function() {
    $('#ajoutprenom').autocomplete('search');
  });
}

function RechargerListeMembres() {
  // Cacher le tableau, afficher l'indicateur de chargement.
  $('#membres').hide();
  $('#membres_wrapper').hide();
  $('#loading').show();


  // Faire la requête au serveur.
  $.ajax({
    url: '/api/membres',
    dataType: 'json',
  }).done(function(data) {
    if (data.status == 'ok') {
      RemplirTableauMembres(data.membres);
    } else {
      AfficherErreur(
          'Erreur lors du téléchargement de la liste de membres:' +
          data.errorstr
      )
    }
  }).fail(function() {
    AfficherErreur('Erreur lors du téléchargement de la liste de membres.');
  });
}

// Par défaut, le autocomplete de jquery cherche partout dans le mot. On
// définit ce filtre pour ne chercher qu'au début d'un mot.
function FiltreAutocompletePrenoms(request, response_cb) {
  response = []
  term = request.term;
  termlen = term.length;
  term = term.toLowerCase();

  for (i in liste_prenoms_membres) {
    prenom = liste_prenoms_membres[i];
    if (prenom.toLowerCase().slice(0, termlen) == term) {
      response.push(prenom);
    }
  }

  response_cb(response);
}


/**
 * Met en place les raccourcis clavier de la page.
 * TODO(simark): modifier les raccourcis claviers lorsqu'on ouvre le dialogue.
 */
function InitialiserRaccourcisClavier() {
  $(document).keypress(function (event) {
    if (event.keyCode == 43) { // '+'
      event.preventDefault();
      $('#boutonajoutmembre').click();
    } else if (event.keyCode == 47) { // '/'
      event.preventDefault();
      $('#membres_filter input').focus();
    }
  });
}

// TODO(simark): clean that up.
$(document).ready(function () {

  $('#boutonajoutmembre').button();
  $('#boutonajoutmembre').click(function () {
    $('#ajoutmembre').dialog('open');
  });

  $('#ajoutmembre').dialog({
    'autoOpen': false,
    'modal': true,
    'height': 'auto',
    'width': 'auto',
    'title': 'Nouveau membre',
    'draggable': false,
    'resizable': false,
  });

  $('input[type="text"][data-default]').each(function (i) {
    defval = $(this).attr('data-default');
    $(this).val(defval);
    $(this).addClass('input-with-default');

    $(this).focus(function () {
      defval = $(this).attr('data-default');
      if ($(this).val() == defval) {
        $(this).val('');
        $(this).removeClass('input-with-default');
      }
    });

    $(this).blur(function () {
      if (!$(this).val()) {
        defval = $(this).attr('data-default');
        $(this).val(defval);
        $(this).addClass('input-with-default');
      }
    });
  });

  $('#typeabonnement').buttonset();
  
  $('#ajoutprovenance').autocomplete({
    source: ['Poly', 'UdeM', 'HEC'],
    minLength: 0,
    delay: 0,
    autoFocus: true,
  }).focus(function() {
    $('#ajoutprovenance').autocomplete('search');
  });

  $('#ajoutlistedenvoi').button().change(function() {
    if ($(this).prop('checked')) {
      $('label[for=ajoutlistedenvoi] span').text('Ajouter à la liste d\'envoi: oui');
    } else {
      $('label[for=ajoutlistedenvoi] span').text('Ajouter à la liste d\'envoi: non');
    }
  });
  $('#ajoutenvoyer').button().click(function (event) {
    event.preventDefault();
    EnvoyerNouveauMembre();
  });

  $('#ajoutreinitialiser').button().click(function (event) {
    event.preventDefault();
    $('#ajoutmembre input[type="text"]').each(function () {
      if ($(this).attr('data-default')) {
        $(this).val($(this).attr('data-default'));
        $(this).addClass('input-with-default');
      } else {
        $(this).val('');
      }
    });
  });
  
  InitialiserRaccourcisClavier();
  InitialiserTableauMembres();
  RechargerListeMembres();
});
