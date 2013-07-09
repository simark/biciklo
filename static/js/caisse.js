
$(document).ready(function () {
 /* $('.input-numero-piece').typeahead({
    source: ["1234 - Ceci cela", "5678 - Autre chose complètement"],
    updater: parseInt, // Ça ne retient que le nombre du début
  });*/

  $('.input-numero-piece').typeahead({
    source: function(query, process) {
      return $.getJSON('/api/pieces', function (data) {
        ret = [];

        console.log(ret);
        for (i in data) {
          ret.push(data[i]['numero'].toString());
        }


        console.log(ret);

        return ret;
      });
    },
    updater: parseInt, // Ça ne retient que le nombre du début
  });

  $('#input-nouvelle-commande').typeahead({
    source: ["37 - Simon Marchi", "445 - Bob L'Éponge-Tremblay"],
    updater: parseInt,
  });

  $('#form-nouvelle-commande').submit(function () {
    console.log( $('#input-nouvelle-commande').val() );
    return false;
  });
});
