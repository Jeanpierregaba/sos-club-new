import { useEffect, useRef, useState } from "react";

import { ErreurApi, MESSAGE_INDISPONIBLE } from "@/lib/api/client";

// Commun aux onglets de la fiche d'un inscrit (spec 045) : chaque onglet charge ses données à son ouverture, puis à
// chaque changement de ses paramètres (page, filtres). `charger` est relu à chaque rendu : seuls les paramètres,
// sérialisés, relancent la requête.
export function useChargement<T>(charger: () => Promise<T>, parametres: unknown[]) {
  const [donnees, setDonnees] = useState<T | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(true);
  const chargeur = useRef(charger);
  chargeur.current = charger;
  const cle = JSON.stringify(parametres);

  useEffect(() => {
    let actif = true;
    setErreur(null);
    setEnCours(true);
    chargeur
      .current()
      .then((resultat) => {
        if (actif) setDonnees(resultat);
      })
      .catch((e: unknown) => {
        if (actif) setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
      })
      .finally(() => {
        if (actif) setEnCours(false);
      });
    return () => {
      actif = false;
    };
  }, [cle]);

  return { donnees, erreur, enCours };
}
