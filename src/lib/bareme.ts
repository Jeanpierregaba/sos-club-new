// Le barème affiché sur le site (spec 022), repris du référentiel « Harmonisation de la gamification » du
// 2026-11-05. L'API détient le barème appliqué (table `bareme`, réglable dans l'admin) : ces montants servent
// seulement à l'annoncer. Un seul endroit, pour que toutes les pages disent la même chose.
export const BAREME = {
  quiz: { eleve: 50, club: 25 },
  questionDuJour: { eleve: 20, club: 10 },
  badge: { eleve: 500, club: 200 },
  certification: { eleve: 1000, club: 500 },
} as const;

// Le parcours de certification : 12 quiz obligatoires et 5 badges.
export const QUIZ_CERTIFICATION = 12;
export const BADGES_CERTIFICATION = 5;

// « +1 000 » avec une espace fine insécable, à l'identique côté serveur et navigateur (sans dépendre d'Intl).
export const points = (n: number) => `+${String(n).replace(/\B(?=(\d{3})+(?!\d))/g, "\u202f")}`;
