// Recherche et regroupements de la carte des clubs (spec 016), à partir de l'annuaire servi par l'API.
import type { DreAnnuaire, TypeEtablissement } from "@/lib/api/client";

// Comparaison sans accents ni majuscules, pour que « agoe » trouve « Agoè ».
export const normaliser = (s: string) =>
  s
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .replace(/’/g, "'")
    .toLowerCase();

export type Entree<D extends DreAnnuaire = DreAnnuaire> = {
  id: string;
  nom: string;
  type: TypeEtablissement;
  iesg: { id: string; nom: string };
  dre: D;
  cle: string;
};

export function indexer<D extends DreAnnuaire>(annuaire: D[]): Entree<D>[] {
  return annuaire.flatMap((dre) =>
    dre.iesg.flatMap((iesg) =>
      iesg.etablissements.map((e) => ({
        ...e,
        iesg: { id: iesg.id, nom: iesg.nom },
        dre,
        cle: normaliser(e.nom),
      })),
    ),
  );
}

// Chaque mot de la recherche doit se trouver dans le nom, comme dans l'API ; moins de 2 lettres, aucun résultat.
export function chercher<E extends { cle: string }>(index: E[], recherche: string): E[] {
  const mots = normaliser(recherche).split(/\s+/).filter(Boolean);
  if (mots.join("").length < 2) return [];
  return index.filter((e) => mots.every((m) => e.cle.includes(m)));
}

// Les types présents dans une liste, dans l'ordre donné, avec leur nombre.
export function compterParType(
  liste: { type: TypeEtablissement }[],
  ordre: TypeEtablissement[],
): { t: TypeEtablissement; n: number }[] {
  return ordre
    .map((t) => ({ t, n: liste.filter((e) => e.type === t).length }))
    .filter((f) => f.n > 0);
}
