import { useEffect, useState } from "react";

import { ErreurApi, MESSAGE_INDISPONIBLE } from "@/lib/api/client";

// Commun aux onglets de la fiche d'un inscrit (spec 045) : chaque onglet charge ses données à son ouverture.
export function useChargement<T>(charger: () => Promise<T>, cles: unknown[]) {
  const [donnees, setDonnees] = useState<T | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  useEffect(() => {
    let actif = true;
    setErreur(null);
    charger()
      .then((resultat) => actif && setDonnees(resultat))
      .catch((e: unknown) => {
        if (actif) setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
      });
    return () => {
      actif = false;
    };
    // Les clés décrivent la requête : `charger` change à chaque rendu.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, cles);

  return { donnees, erreur };
}
