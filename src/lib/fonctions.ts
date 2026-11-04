import type { EtatVerification, Fonction } from "@/lib/api/client";

// Les fonctions d'un encadreur (spec 018). La valeur est celle de l'API.
export const FONCTIONS: { valeur: Fonction; libelle: string }[] = [
  { valeur: "enseignant", libelle: "Enseignant ou enseignante" },
  { valeur: "responsable", libelle: "Responsable pédagogique ou administratif" },
  { valeur: "sante", libelle: "Infirmier, infirmière ou agent de santé scolaire" },
  { valeur: "accompagnateur", libelle: "Accompagnateur ou animateur" },
  { valeur: "autre", libelle: "Autre fonction" },
];

export const libelleFonction = (fonction: Fonction, precision?: string | null) =>
  fonction === "autre" && precision
    ? precision
    : (FONCTIONS.find((f) => f.valeur === fonction)?.libelle ?? fonction);

export const LIBELLES_VERIFICATION: Record<EtatVerification, string> = {
  en_attente: "En attente de vérification",
  actif: "Vérifié",
  refuse: "Refusé",
};
