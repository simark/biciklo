function MarquerFaits() {
  for (i in membres_id) {
    numero = membres_id[i];
   
    $.ajax({
      url: '/api/membres/' + numero,
      type: 'PUT',
      dataType: 'json',
      data: {'listedenvoi': 'fait'},
      }).done(function (data, textStatus, jqXHR) {
        AfficherSucces('Fait !');
    }).fail(DisplayError);
  }
}

$(document).ready(function() {
	$('#marquer-faits').click(MarquerFaits);
});
