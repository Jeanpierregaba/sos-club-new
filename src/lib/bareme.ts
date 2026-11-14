// Le barème affiché sur le site (spec 034, cahier des charges du 2026-11-10) : le club reçoit toujours la moitié du
// gain de l'élève. L'API détient le barème appliqué (table `bareme`, réglable dans l'admin) : ces montants servent
// seulement à l'annoncer. Un seul endroit, pour que toutes les pages disent la même chose.
export const BAREME = {
  quiz: { eleve: 50, club: 25 },
  // Spec 034 : un quiz de certification validé à 10/10.
  quizCertification: { eleve: 50, club: 25 },
  questionDuJour: { eleve: 20, club: 10 },
  badge: { eleve: 500, club: 250 },
  certification: { eleve: 1000, club: 500 },
} as const;

// Les 4 niveaux des 100 quiz Jeux (spec 034) : nombre de quiz, gain d'un quiz réussi et bonus de l'étoile du niveau,
// pour l'élève ; son club reçoit la moitié.
export type NiveauJeux = "debutant" | "intermediaire" | "avance" | "expert";
export const NIVEAUX_JEUX: {
  code: NiveauJeux;
  nom: string;
  quiz: number;
  eleve: number;
  etoile: number;
}[] = [
  { code: "debutant", nom: "Débutant", quiz: 40, eleve: 50, etoile: 500 },
  { code: "intermediaire", nom: "Intermédiaire", quiz: 30, eleve: 100, etoile: 1000 },
  { code: "avance", nom: "Avancé", quiz: 20, eleve: 150, etoile: 1500 },
  { code: "expert", nom: "Expert", quiz: 10, eleve: 200, etoile: 3000 },
];
export const MAX_POINTS_QUIZ = NIVEAUX_JEUX.reduce((n, x) => n + x.quiz * x.eleve, 0);
export const MAX_POINTS_ETOILES = NIVEAUX_JEUX.reduce((n, x) => n + x.etoile, 0);

// Le parcours de certification (spec 034) : 20 quiz obligatoires, à 10/10, et 5 badges.
export const QUIZ_CERTIFICATION = 20;
export const BADGES_CERTIFICATION = 5;

// « +1 000 » avec une espace fine insécable, à l'identique côté serveur et navigateur (sans dépendre d'Intl).
export const points = (n: number) => `+${String(n).replace(/\B(?=(\d{3})+(?!\d))/g, "\u202f")}`;
