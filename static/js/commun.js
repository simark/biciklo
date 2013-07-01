function SupprimerRaccourcisClavier() {
  $(document).unbind('keypress');
  $(document).unbind('keydown');
  $(document).unbind('keyup');
}

function ObtenirChoixProvenance() {
  return ["Poly", "UdeM", "HEC", "Autre"];
}

function InitCommun() {

}
