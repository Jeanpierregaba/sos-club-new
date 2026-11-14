import { useState } from "react";

import { chargerBibliotheque, type Parcours, type QuizEntree } from "@/lib/api/client";
import type { NiveauJeux } from "@/lib/bareme";

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
  niveau?: NiveauJeux | null;
}) {
  const [parcours, setParcours] = useState<Parcours>(depart?.parcours ?? "jeux");
  const [place, setPlace] = useState(depart?.place ?? 1);
  const [ressource, setRessource] = useState(depart?.ressource_id ?? "");
  // Spec 034 : le niveau d'un quiz Jeux fixe ses points et l'étoile à laquelle il compte.
  const [niveau, setNiveau] = useState<NiveauJeux>(depart?.niveau ?? "debutant");
  const entree: Pick<QuizEntree, "parcours" | "place" | "ressource_id" | "niveau"> =
    parcours === "certification"
      ? { parcours, place, ressource_id: ressource || null, niveau: null }
      : { parcours, place: null, ressource_id: null, niveau };
  const ressourceTitre = depart?.ressource_titre ?? null;
  return {
    parcours,
    setParcours,
    place,
    setPlace,
    ressource,
    setRessource,
    ressourceTitre,
    niveau,
    setNiveau,
    entree,
  };
}
