function SupprimerRaccourcisClavier() {
  $(document).unbind('keypress');
  $(document).unbind('keydown');
  $(document).unbind('keyup');
}

function ObtenirChoixProvenance() {
  return ["Poly", "UdeM", "HEC", "Autre"];
}

/*
 * liste_json: liste de lignes (liste de dict)
 * tableau: objet jquery du <table>
 */
function RemplirTableauGenerique(liste_lignes, tableau) {
  // Vider le contenu actuel
  tableau.dataTable().fnClearTable();

  // Info sur les colonnes
  var colonnes = []

  // Les lignes qui seront envoyées à datatable
  var lignes = new Array();

  // Aller chercher les infos sur les colonnes
  tableau.find('th').each(function(i) {
    colonnes.push({
      // Nom de la colonne où aller chercher l'info
      source: $(this).attr('data-column'),
      // Fonction de transformation à appliquer
      transform: $(this).attr('data-transform'),
    });
  });

  // Obtenir les fonctions de génération des classes et id
  rowClassCallback = tableau.attr('data-row-class-callback');
  if (rowClassCallback)
    rowClassCallback = window[rowClassCallback]

  rowIdCallback = tableau.attr('data-row-id-callback');
  if (rowIdCallback)
    rowIdCallback = window[rowIdCallback]

  // Créer les lignes une par une
  for (i in liste_lignes) {
    var ligne_data = liste_lignes[i];
    var ligne = {};

    // Créer le tableau de cellules pour cette ligne
    idx = 0;
    for (col in colonnes) {
      var colname = colonnes[col].source;
      var transform = colonnes[col].transform;
      var valeur = null;

      if (colname in ligne_data) {
        valeur = ligne_data[colname];
      }

      if (transform && transform in window && typeof(window[transform] == "function")) {
        valeur = window[transform](valeur);
      }

      ligne[idx] = valeur;
      idx++;
    }

    if (rowClassCallback) {
      className = rowClassCallback(ligne_data);
      if (className) {
        ligne.DT_RowClass = className;
      }
    }

    if (rowIdCallback) {
      id = rowIdCallback(ligne_data);
      if (id) {
        ligne.DT_RowId = id;
      }
    }

    lignes.push(ligne);
  }

  // Ajouter les lignes au tableau.
  tableau.dataTable().fnAddData(lignes);
}

function NombreVersPrix(str) {
  var int = parseInt(str);
  var ret = "";

  if (!str || str === "") {
    return "";
  }

  if (int < 0) {
    int = -int;
    ret += "-";
  }

  cennes = (int % 100).toString();
  dollars = ((int - cennes) / 100).toString();

  if (cennes.length == 1) {
    cennes = "0" + cennes;
  }

  ret += dollars + "," + cennes + "&nbsp;$";
  return ret;
}

function FormatDate(obj) {
  if (!obj || !obj['$date'])
    return '?';

  d = new Date(obj['$date'])
  year = d.getFullYear();
  month = d.getMonth() + 1;
  if (month < 10)
    month = '0' + month;
  day = d.getDate();
  if (day < 10)
    day = '0' + day;

  return year + "-" + month + "-" + day;
}

function DisplayError(jqXHR, textStatus, errorThrown) {
  data = jqXHR.responseText;
  AfficherErreur(JSON.parse(data));
}

function InitCommun() {

}
