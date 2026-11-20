import type { InscritDetail, ModificationInscrit } from "@/lib/api/client";

// Spec 045 : la modification d'un inscrit par l'équipe.

export type Valeurs = {
  prenom: string;
  nom: string;
  email: string;
  telephone: string;
  classe: string;
  fonction: string;
  fonction_precision: string;
  discipline: string;
  commune: string;
};

export const MOTIF_MIN = 10;

export function valeursDe(inscrit: InscritDetail): Valeurs {
  return {
    prenom: inscrit.prenom,
    nom: inscrit.nom,
    email: inscrit.email ?? "",
    telephone: inscrit.telephone ?? "",
    classe: inscrit.eleve?.classe ?? "",
    fonction: inscrit.encadreur?.fonction ?? "",
    fonction_precision: inscrit.encadreur?.fonction_precision ?? "",
    discipline: inscrit.encadreur?.discipline ?? "",
    commune: inscrit.encadreur?.commune ?? "",
  };
}

// Seuls les champs changés partent : l'API ne touche qu'à eux (spec 045).
export function entreeDe(
  inscrit: InscritDetail,
  valeurs: Valeurs,
  motif: string,
): ModificationInscrit {
  const avant = valeursDe(inscrit);
  const entree: ModificationInscrit = { motif: motif.trim(), version: inscrit.version ?? null };
  const champs: (keyof Valeurs)[] = ["prenom", "nom", "email", "telephone"];
  if (inscrit.eleve) champs.push("classe");
  if (inscrit.encadreur) champs.push("fonction", "fonction_precision", "discipline", "commune");
  for (const champ of champs) {
    if (valeurs[champ].trim() !== avant[champ].trim()) {
      (entree as Record<string, unknown>)[champ] = valeurs[champ].trim();
    }
  }
  return entree;
}
