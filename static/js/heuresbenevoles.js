function RechargerListeHeures() {
  // Cacher le tableau, afficher l'indicateur de chargement.
  $('#heuresbenevoles').hide();
  $('#heuresbenevoles_wrapper').hide();
  $('#loading').show();

  // Faire la requête au serveur.
  $.get('/api/benevoles').done(function(data, textStatus, jqXHR) {
    RemplirListeHeures(data);
  }).fail(DisplayError);
}

function RemplirListeHeures(benevoles_json) {
  tableau = $('#heuresbenevoles');

  lignes = []

  for (i in benevoles_json) {
    benevole = benevoles_json[i];
    for (j in benevole.heuresbenevole) {
      ligne = benevole.heuresbenevole[j];

      lignes.push({
        date: ligne.date,
        nom: benevole.prenom + " " + benevole.nom,
        activite: ligne.raison,
        heures: ligne.heures,
      });
    }
  }
  console.log(lignes);

  RemplirTableauGenerique(lignes, tableau);

  // Afficher le tableau, cacher l'indicateur de chargement.
  $('#loading').hide();
  $('#heuresbenevoles').show();
  $('#heuresbenevoles_wrapper').show();
}

$(document).ready(function() {
  $('#formulaireheuresbenevoles').submit(function(){
    var data = {};
    var numero = $('#benevole').val();
    data['heures'] = $('#heures').val();
    data['raison'] = $('#raison').val();
    console.log(data);
    $.post('/api/membres/' + numero + '/heuresbenevoles', data)
    .done(function (resultat, textStatus, jqXHR) {
      AfficherSucces("Heures ajoutées");
      RechargerListeHeures();
    })
    .fail(DisplayError);

    return false;
  });

  $('#heuresbenevoles').dataTable({
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
    }
  });

  RechargerListeHeures();
});
