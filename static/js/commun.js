function SupprimerRaccourcisClavier() {
  $(document).unbind('keypress');
  $(document).unbind('keydown');
  $(document).unbind('keyup');
}

function InitChampsAvecValeurParDefaut() {
  // Initialiser champs avec valeur par défaut (description).
  $('input[type="text"][data-default]').each(function (i) {
    defval = $(this).attr('data-default');
    $(this).val(defval);
    $(this).addClass('with-default');

    $(this).focus(function () {
      defval = $(this).attr('data-default');
      if ($(this).val() == defval) {
        $(this).val('');
        $(this).removeClass('with-default');
      }
    });

    $(this).blur(function () {
      if (!$(this).val()) {
        defval = $(this).attr('data-default');
        $(this).val(defval);
        $(this).addClass('with-default');
      }
    });
  });
}

function InitCommun() {
  InitChampsAvecValeurParDefaut();
}
