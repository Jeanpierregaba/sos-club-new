import type { EtatContenu, Signature } from "@/lib/api/client";

// États d'un contenu modéré (spec 023), lisibles sans la couleur : chaque pastille a son libellé.
export const ETATS: Record<EtatContenu, { libelle: string; classe: string }> = {
  brouillon: { libelle: "Brouillon", classe: "bg-muted text-ink/70" },
  en_attente: { libelle: "En attente de modération", classe: "bg-sun/30 text-ink" },
  a_corriger: { libelle: "À corriger", classe: "bg-tangerine/20 text-ink" },
  refuse: { libelle: "Refusé", classe: "bg-logo-red/15 text-logo-red" },
  publie: { libelle: "Publié", classe: "bg-leaf/20 text-ink" },
  depublie: { libelle: "Retiré du site", classe: "bg-logo-red/15 text-logo-red" },
};

export const LIMITES = { titre: 120, chapo: 300, texte: 20_000 } as const;

export function signer(signature: Signature) {
  if (signature.profil === "eleve")
    return signature.club ? `${signature.nom} · ${signature.club}` : signature.nom;
  return signature.fonction ? `${signature.nom}, ${signature.fonction}` : signature.nom;
}
