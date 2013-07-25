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
  colonnes = []

  // Les lignes qui seront envoyées à datatable
  lignes = new Array();

  // Aller chercher les infos sur les colonnes
  tableau.find('th').each(function(i) {
    colonnes.push({
      // Nom de la colonne où aller chercher l'info
      source: $(this).attr('data-column'),
      // Fonction de transformation à appliquer
      transform: $(this).attr('data-transform'),
    });
  });

  // Créer les lignes une par une
  for (i in liste_lignes) {
    ligne_data = liste_lignes[i];
    ligne = new Array();

    // Créer le tableau de cellules pour cette ligne
    for (col in colonnes) {
      colname = colonnes[col].source;
      transform = colonnes[col].transform;

      if (colname in ligne_data) {
        valeur = ligne_data[colname];
        if (transform && transform in window && typeof(window[transform] == "function")) {
          valeur = window[transform](valeur);
        }
        ligne.push(valeur);
      } else {
        ligne.push('?');
      }
    }
    lignes.push(ligne);
  }

  // Ajouter les lignes au tableau.
  tableau.dataTable().fnAddData(lignes);
}

function NombreVersPrix(str) {
  int = parseInt(str);
  cennes = (int % 100).toString();
  dollars = ((int - cennes) / 100).toString();

  if (cennes.length == 1) {
    cennes = "0" + cennes;
  }

  return dollars + "," + cennes + " $";
}

function DisplayError(jqXHR, textStatus, errorThrown) {
  data = jqXHR.responseText;
  AfficherErreur(JSON.parse(data));
}

function InitCommun() {

}
