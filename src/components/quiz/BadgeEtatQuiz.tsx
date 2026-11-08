import type { EtatQuiz } from "@/lib/api/client";

export const ETATS_QUIZ: Record<EtatQuiz, { libelle: string; classe: string }> = {
  brouillon: { libelle: "Brouillon", classe: "bg-muted text-muted-foreground" },
  soumis: { libelle: "À publier", classe: "bg-sun/30 text-ink" },
  publie: { libelle: "En ligne", classe: "bg-primary/15 text-primary" },
  depublie: { libelle: "Dépublié", classe: "bg-logo-red/10 text-logo-red" },
};

export function BadgeEtatQuiz({ etat }: { etat: EtatQuiz }) {
  const { libelle, classe } = ETATS_QUIZ[etat];
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-extrabold ${classe}`}
    >
      {libelle}
    </span>
  );
}
