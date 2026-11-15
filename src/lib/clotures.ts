import type { ClotureResume } from "@/lib/api/client";

// Les états d'une clôture de semestre (spec 037) et leur pastille.
export const ETATS_CLOTURE: Record<ClotureResume["etat"], { libelle: string; classe: string }> = {
  ouvert: { libelle: "Ouvert", classe: "bg-mist-soft text-ink" },
  gele: { libelle: "Gelé", classe: "bg-sky/20 text-logo-blue" },
  valide: { libelle: "Validé", classe: "bg-sun/40 text-ink" },
  publie: { libelle: "Publié", classe: "bg-primary/15 text-primary" },
};
