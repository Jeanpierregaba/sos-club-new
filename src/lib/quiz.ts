import type { NiveauJeux } from "@/lib/bareme";

// Catalogue des 80 quiz Jeux de la banque officielle des Clubs Santé (spec 049), dans les 4 parties du document.
// Chaque quiz pose 10 questions d'une même partie et d'une même difficulté ; son numéro (1 à 80) et son niveau sont
// ceux de `backend/alembic/donnees/banque_officielle.json`, que la migration a chargés (un test le vérifie).
// Les questions elles-mêmes restent côté API : le serveur seul arbitre les quiz (ADR-0004).

export type QuizCatalogue = { t: string; n: number; niveau: NiveauJeux };

export type Pole = {
  id: string;
  nom: string;
  sur: string;
  d: string;
  themes: string[];
  couleur: string;
  quiz: QuizCatalogue[];
};

export const poles: Pole[] = [
  {
    id: "sante-publique",
    nom: "Santé publique",
    sur: "Partie 1 · questions 1 à 300",
    d: "Maladies, vaccination, prévention et corps humain : les bases de la santé des populations.",
    themes: ["OMS et santé publique", "Paludisme et tuberculose", "Vaccination", "Corps humain"],
    couleur: "var(--logo-blue)",
    quiz: [
      { t: "Santé publique — quiz 1", n: 1, niveau: "debutant" },
      { t: "Santé publique — quiz 2", n: 5, niveau: "debutant" },
      { t: "Santé publique — quiz 3", n: 9, niveau: "debutant" },
      { t: "Santé publique — quiz 4", n: 12, niveau: "debutant" },
      { t: "Santé publique — quiz 5", n: 16, niveau: "debutant" },
      { t: "Santé publique — quiz 6", n: 20, niveau: "debutant" },
      { t: "Santé publique — quiz 7", n: 21, niveau: "debutant" },
      { t: "Santé publique — quiz 8", n: 25, niveau: "debutant" },
      { t: "Santé publique — quiz 9", n: 29, niveau: "debutant" },
      { t: "Santé publique — quiz 10", n: 32, niveau: "debutant" },
      { t: "Santé publique — quiz 11", n: 36, niveau: "intermediaire" },
      { t: "Santé publique — quiz 12", n: 40, niveau: "intermediaire" },
      { t: "Santé publique — quiz 13", n: 41, niveau: "intermediaire" },
      { t: "Santé publique — quiz 14", n: 45, niveau: "intermediaire" },
      { t: "Santé publique — quiz 15", n: 49, niveau: "intermediaire" },
      { t: "Santé publique — quiz 16", n: 52, niveau: "intermediaire" },
      { t: "Santé publique — quiz 17", n: 56, niveau: "intermediaire" },
      { t: "Santé publique — quiz 18", n: 60, niveau: "avance" },
      { t: "Santé publique — quiz 19", n: 61, niveau: "avance" },
      { t: "Santé publique — quiz 20", n: 65, niveau: "avance" },
      { t: "Santé publique — quiz 21", n: 68, niveau: "avance" },
      { t: "Santé publique — quiz 22", n: 69, niveau: "avance" },
      { t: "Santé publique — quiz 23", n: 73, niveau: "expert" },
      { t: "Santé publique — quiz 24", n: 76, niveau: "expert" },
      { t: "Santé publique — quiz 25", n: 80, niveau: "expert" },
    ],
  },
  {
    id: "sante-sexuelle-reproductive",
    nom: "Santé sexuelle et reproductive",
    sur: "Partie 2 · questions 301 à 550",
    d: "IST, contraception, cycle et appareil reproducteur : connaître son corps pour se protéger.",
    themes: ["IST et VIH", "Contraception", "Cycle menstruel", "Grossesse"],
    couleur: "var(--rose)",
    quiz: [
      { t: "Santé sexuelle et reproductive — quiz 1", n: 2, niveau: "debutant" },
      { t: "Santé sexuelle et reproductive — quiz 2", n: 6, niveau: "debutant" },
      { t: "Santé sexuelle et reproductive — quiz 3", n: 10, niveau: "debutant" },
      { t: "Santé sexuelle et reproductive — quiz 4", n: 14, niveau: "debutant" },
      { t: "Santé sexuelle et reproductive — quiz 5", n: 18, niveau: "debutant" },
      { t: "Santé sexuelle et reproductive — quiz 6", n: 22, niveau: "debutant" },
      { t: "Santé sexuelle et reproductive — quiz 7", n: 26, niveau: "debutant" },
      { t: "Santé sexuelle et reproductive — quiz 8", n: 30, niveau: "debutant" },
      { t: "Santé sexuelle et reproductive — quiz 9", n: 34, niveau: "intermediaire" },
      { t: "Santé sexuelle et reproductive — quiz 10", n: 38, niveau: "intermediaire" },
      { t: "Santé sexuelle et reproductive — quiz 11", n: 42, niveau: "intermediaire" },
      { t: "Santé sexuelle et reproductive — quiz 12", n: 46, niveau: "intermediaire" },
      { t: "Santé sexuelle et reproductive — quiz 13", n: 50, niveau: "intermediaire" },
      { t: "Santé sexuelle et reproductive — quiz 14", n: 54, niveau: "intermediaire" },
      { t: "Santé sexuelle et reproductive — quiz 15", n: 58, niveau: "avance" },
      { t: "Santé sexuelle et reproductive — quiz 16", n: 62, niveau: "avance" },
      { t: "Santé sexuelle et reproductive — quiz 17", n: 66, niveau: "avance" },
      { t: "Santé sexuelle et reproductive — quiz 18", n: 70, niveau: "avance" },
      { t: "Santé sexuelle et reproductive — quiz 19", n: 74, niveau: "expert" },
      { t: "Santé sexuelle et reproductive — quiz 20", n: 78, niveau: "expert" },
    ],
  },
  {
    id: "journees-mondiales",
    nom: "Journées mondiales de la santé",
    sur: "Partie 3 · questions 551 à 750",
    d: "Le calendrier des journées et campagnes mondiales de santé, mois après mois.",
    themes: [
      "Journée mondiale de la santé",
      "Calendrier de l'OMS",
      "Campagnes du mois",
      "Journées de l'ONU",
    ],
    couleur: "var(--tangerine)",
    quiz: [
      { t: "Journées mondiales de la santé — quiz 1", n: 4, niveau: "debutant" },
      { t: "Journées mondiales de la santé — quiz 2", n: 8, niveau: "debutant" },
      { t: "Journées mondiales de la santé — quiz 3", n: 13, niveau: "debutant" },
      { t: "Journées mondiales de la santé — quiz 4", n: 17, niveau: "debutant" },
      { t: "Journées mondiales de la santé — quiz 5", n: 24, niveau: "debutant" },
      { t: "Journées mondiales de la santé — quiz 6", n: 28, niveau: "debutant" },
      { t: "Journées mondiales de la santé — quiz 7", n: 33, niveau: "intermediaire" },
      { t: "Journées mondiales de la santé — quiz 8", n: 37, niveau: "intermediaire" },
      { t: "Journées mondiales de la santé — quiz 9", n: 44, niveau: "intermediaire" },
      { t: "Journées mondiales de la santé — quiz 10", n: 48, niveau: "intermediaire" },
      { t: "Journées mondiales de la santé — quiz 11", n: 53, niveau: "intermediaire" },
      { t: "Journées mondiales de la santé — quiz 12", n: 57, niveau: "avance" },
      { t: "Journées mondiales de la santé — quiz 13", n: 64, niveau: "avance" },
      { t: "Journées mondiales de la santé — quiz 14", n: 71, niveau: "avance" },
      { t: "Journées mondiales de la santé — quiz 15", n: 77, niveau: "expert" },
    ],
  },
  {
    id: "evss",
    nom: "EVSS",
    sur: "Partie 4 · questions 751 à 1000",
    d: "Éducation à la vie sexuelle et à la santé : droits, consentement, prévention des violences.",
    themes: [
      "Droits sexuels",
      "Consentement",
      "Violences basées sur le genre",
      "Comportements à risque",
    ],
    couleur: "var(--primary)",
    quiz: [
      { t: "EVSS — quiz 1", n: 3, niveau: "debutant" },
      { t: "EVSS — quiz 2", n: 7, niveau: "debutant" },
      { t: "EVSS — quiz 3", n: 11, niveau: "debutant" },
      { t: "EVSS — quiz 4", n: 15, niveau: "debutant" },
      { t: "EVSS — quiz 5", n: 19, niveau: "debutant" },
      { t: "EVSS — quiz 6", n: 23, niveau: "debutant" },
      { t: "EVSS — quiz 7", n: 27, niveau: "debutant" },
      { t: "EVSS — quiz 8", n: 31, niveau: "debutant" },
      { t: "EVSS — quiz 9", n: 35, niveau: "intermediaire" },
      { t: "EVSS — quiz 10", n: 39, niveau: "intermediaire" },
      { t: "EVSS — quiz 11", n: 43, niveau: "intermediaire" },
      { t: "EVSS — quiz 12", n: 47, niveau: "intermediaire" },
      { t: "EVSS — quiz 13", n: 51, niveau: "intermediaire" },
      { t: "EVSS — quiz 14", n: 55, niveau: "intermediaire" },
      { t: "EVSS — quiz 15", n: 59, niveau: "avance" },
      { t: "EVSS — quiz 16", n: 63, niveau: "avance" },
      { t: "EVSS — quiz 17", n: 67, niveau: "avance" },
      { t: "EVSS — quiz 18", n: 72, niveau: "avance" },
      { t: "EVSS — quiz 19", n: 75, niveau: "expert" },
      { t: "EVSS — quiz 20", n: 79, niveau: "expert" },
    ],
  },
];

// Le niveau de chaque quiz par son numéro : la page reste lisible quand l'API ne répond pas.
export const niveauParNumero: Map<number, NiveauJeux> = new Map(
  poles.flatMap((p) => p.quiz.map((q) => [q.n, q.niveau] as const)),
);
