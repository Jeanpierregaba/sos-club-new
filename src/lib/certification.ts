import type { BadgeParcours, EtatCertificat, PlaceParcours } from "@/lib/api/client";

// Certification Génie Imhotep (spec 029) : libellés et règles d'affichage du parcours. L'API décide seule de ce qui
// est ouvert, réussi ou délivré ; le site ne fait que le montrer.

export const ETATS_PLACE: Record<PlaceParcours["etat"], { libelle: string; classe: string }> = {
  reussie: { libelle: "Réussi", classe: "bg-primary/15 text-primary" },
  ouverte: { libelle: "À jouer", classe: "bg-sun/30 text-ink" },
  verrouillee: { libelle: "Verrouillé", classe: "bg-mist text-muted-foreground" },
  bientot: { libelle: "Bientôt disponible", classe: "bg-mist text-muted-foreground" },
};

export const ETATS_CERTIFICAT: Record<EtatCertificat, { libelle: string; classe: string }> = {
  valide: { libelle: "Valide", classe: "bg-primary/15 text-primary" },
  revoque: { libelle: "Révoqué", classe: "bg-logo-red/15 text-logo-red" },
  remplace: { libelle: "Remplacé", classe: "bg-mist text-muted-foreground" },
};

// Les dégradés des cinq badges, du bronze au diamant, comme sur la page /certification.
export const FONDS_BADGES = [
  "from-tangerine to-bark",
  "from-[oklch(0.82_0.02_257)] to-[oklch(0.58_0.03_257)]",
  "from-sun to-tangerine",
  "from-[oklch(0.85_0.04_200)] to-sky",
  "from-sky to-grape",
] as const;

export const fondBadge = (rang: number) => FONDS_BADGES[rang - 1] ?? FONDS_BADGES[0];

// Une place se joue si un quiz y est publié et qu'elle est ouverte, ou déjà réussie (rejouer pour s'entraîner).
export const jouable = (place: PlaceParcours) =>
  place.quiz_id !== null && (place.etat === "ouverte" || place.etat === "reussie");

// Le prochain badge à décrocher et le nombre de quiz qui manquent ; null quand tous sont obtenus.
export function prochainBadge(
  badges: BadgeParcours[],
  reussies: number,
): { badge: BadgeParcours; manquent: number } | null {
  const badge = badges.find((b) => b.obtenu_le === null);
  return badge ? { badge, manquent: Math.max(0, badge.palier - reussies) } : null;
}

export const quizRestants = (n: number) => (n === 1 ? "1 quiz" : `${n} quiz`);

// « Jean K. » : un encadreur n'apparaît publiquement que par son prénom et l'initiale de son nom.
export const nomPublicEncadreur = (prenom: string, initiale: string) => `${prenom} ${initiale}`;
