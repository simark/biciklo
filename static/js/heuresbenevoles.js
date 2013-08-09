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
    })
    .fail(DisplayError);

    return false;
  });
});
