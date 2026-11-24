import type { EtatVerification, Fonction } from "@/lib/api/client";
import { m } from "@/paraglide/messages.js";

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

// Les mêmes fonctions dans la langue de la page (spec 052), pour les pages publiques.
const NOMS_FONCTIONS: Record<Fonction, () => string> = {
  enseignant: m.fonction_enseignant,
  responsable: m.fonction_responsable,
  sante: m.fonction_sante,
  accompagnateur: m.fonction_accompagnateur,
  autre: m.fonction_autre,
};
export const nomFonction = (fonction: Fonction, precision?: string | null) =>
  fonction === "autre" && precision ? precision : (NOMS_FONCTIONS[fonction]?.() ?? fonction);
