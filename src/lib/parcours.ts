import { useState } from "react";

import { chargerBibliotheque, type Parcours, type QuizEntree } from "@/lib/api/client";

export type FasciculeChoix = { id: string; titre: string };

// Les fascicules publiés de la bibliothèque, à relier à un quiz de certification (spec 029).
export const chargerFascicules = (): Promise<FasciculeChoix[]> =>
  chargerBibliotheque({ categorie: "fascicule" })
    .then((b) => b.ressources.map((r) => ({ id: r.id, titre: r.titre })))
    .catch(() => []);

// L'état des champs du parcours d'un quiz, et ce qu'ils ajoutent à l'entrée envoyée à l'API.
export function useParcours(depart?: {
  parcours: Parcours;
  place: number | null;
  ressource_id: string | null;
  ressource_titre?: string | null;
}) {
  const [parcours, setParcours] = useState<Parcours>(depart?.parcours ?? "jeux");
  const [place, setPlace] = useState(depart?.place ?? 1);
  const [ressource, setRessource] = useState(depart?.ressource_id ?? "");
  const entree: Pick<QuizEntree, "parcours" | "place" | "ressource_id"> =
    parcours === "certification"
      ? { parcours, place, ressource_id: ressource || null }
      : { parcours, place: null, ressource_id: null };
  const ressourceTitre = depart?.ressource_titre ?? null;
  return {
    parcours,
    setParcours,
    place,
    setPlace,
    ressource,
    setRessource,
    ressourceTitre,
    entree,
  };
}
