var liste_prenoms_membres = [];

/**
 * Lis et retourne les champs du formulaire d'inscription d'un membre.
 *
 * @return Objet possédant les clés/valeurs à envoyer au serveur.
 */
function LireChampsAjoutMembre() {
  request_data = {};

  request_data.prenom = $('#ajoutprenom').val();
  request_data.nom = $('#ajoutnom').val();
  request_data.courriel = $('#ajoutcourriel').val();
  request_data.provenance = $('#ajoutprovenance').val();
  request_data.listedenvoi = ($('#ajoutlistedenvoi').prop('checked')) ? 'oui' : 'non';
  
  return request_data;
}

/**
 * Envoie une requête d'ajout d'un membre au serveur.
 */
function EnvoyerAjoutMembre() {
  donnees_requete = LireChampsAjoutMembre();

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
function InitListeMembres() {
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


/**
 * Remplis la liste des membres à partir de la liste JSON reçue du serveur.
 */
function RemplirTableauMembres(membres_json) {
  tableau = $('#membres');
  
  // Vider le contenu actuel
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
    if ('prenom' in membre_json) prenoms_vus[membre_json.prenom] = 1;

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
  }).done(function(data) {
    if (data.status == 'ok') {
      // Remplir le tableau.
      RemplirTableauMembres(data.membres);
    } else {
      AfficherErreur(
          'Erreur lors du téléchargement de la liste de membres:' +
          data.errorstr)
    }
  }).fail(function() {
    AfficherErreur('Erreur lors du téléchargement de la liste de membres.');
  });
}

/**
 * Filtre pour autocomplete de JQuery. Par défaut, if cherche partout dans le
 * mot. On définit ce filtre pour ne chercher qu'au début d'un mot.
 */
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
 * Effectue la transition vers le mode normal.
 */
function ModeNormal() {
  $('#ajoutmembre').dialog('close');

  SupprimerRaccourcisClavier();
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

/**
 * Effectue la transition vers le mode ajout d'un membre.
 */
function ModeAjout() {
  $('#ajoutmembre').dialog('open');
  
  SupprimerRaccourcisClavier();
  $(document).keyup(function (event) {
    if (event.keyCode == 27) { // escape
      ModeNormal();
    }
  });
}

/**
 * Initialise ce qui est en lien avec le formulaire d'ajout d'un membre.
 */
function InitFormulaireAjoutMembre() {
  // Boutons ajout membre
  $('#boutonajoutmembre').button().click(function () {
    ModeAjout();
  });

  // Dialogue ajout membre.
  $('#ajoutmembre').dialog({
    'autoOpen': false,
    'modal': true,
    'height': 'auto',
    'width': 'auto',
    'title': 'Ajout d\'un membre',
    'draggable': false,
    'resizable': false,
  });

  
  // Bouton provenance
  $('#ajoutprovenance').autocomplete({
    source: ['Poly', 'UdeM', 'HEC'],
    minLength: 0,
    delay: 0,
    autoFocus: true,
  }).focus(function() {
    $('#ajoutprovenance').autocomplete('search');
  });

  // Bouton liste d'envoi
  $('#ajoutlistedenvoi').button().change(function() {
    if ($(this).prop('checked')) {
      $('label[for=ajoutlistedenvoi] span').text('Ajouter à la liste d\'envoi: oui');
    } else {
      $('label[for=ajoutlistedenvoi] span').text('Ajouter à la liste d\'envoi: non');
    }
  });

  // Bouton submit
  $('#ajoutenvoyer').button().click(function (event) {
    event.preventDefault();
    EnvoyerAjoutMembre();
  });

  // Bouton reset
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
}

$(document).ready(function () {
  InitCommun();

  InitFormulaireAjoutMembre(); 
  InitListeMembres();
  RechargerListeMembres();
  
  ModeNormal();
});

