import type { Classe } from "@/lib/api/client";

// Les classes du secondaire, dans l'ordre (spec 017). La valeur est celle de l'API.
export const CLASSES: { valeur: Classe; libelle: string }[] = [
  { valeur: "6e", libelle: "6e" },
  { valeur: "5e", libelle: "5e" },
  { valeur: "4e", libelle: "4e" },
  { valeur: "3e", libelle: "3e" },
  { valeur: "2nde", libelle: "2nde" },
  { valeur: "1re", libelle: "1re" },
  { valeur: "tle", libelle: "Terminale" },
];

export const libelleClasse = (classe: Classe) =>
  CLASSES.find((c) => c.valeur === classe)?.libelle ?? classe;
