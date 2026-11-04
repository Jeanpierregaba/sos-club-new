import type { EtablissementChoisi } from "@/components/ChoixEtablissement";

// Un établissement de la liste, ou une proposition (DRE, IESG, nom) que l'équipe nationale vérifiera (spec 017).
export type SaisieEtablissement = {
  choix: EtablissementChoisi | null;
  proposer: boolean;
  dre: string;
  iesg: string;
  nom: string;
};

export const SAISIE_VIDE: SaisieEtablissement = {
  choix: null,
  proposer: false,
  dre: "",
  iesg: "",
  nom: "",
};

export const manqueEtablissement = (s: SaisieEtablissement) => {
  if (!s.proposer && !s.choix) return "Choisis ton établissement dans la liste.";
  if (s.proposer && (!s.iesg || s.nom.trim().length < 2))
    return "Indique ta DRE, ton inspection et le nom de ton établissement.";
  return null;
};

export const corpsEtablissement = (s: SaisieEtablissement) =>
  s.proposer
    ? { proposition: { iesg_id: s.iesg, nom: s.nom } }
    : { etablissement_id: s.choix?.id ?? null };
