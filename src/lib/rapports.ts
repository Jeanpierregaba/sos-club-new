import type { ModeleRapport, RapportResume } from "@/lib/api/client";

// Rapports (spec 038) : libellés des modèles, des états et des champs, partagés par l'espace et l'admin.
export const MODELES: Record<ModeleRapport, { libelle: string; aide: string; points: string }> = {
  activite: {
    libelle: "Rapport d'activité",
    aide: "Une activité réalisée par le club : causerie, sensibilisation, dépistage…",
    points: "+100 pour l'encadreur auteur et +50 pour le club à l'approbation.",
  },
  mensuel: {
    libelle: "Rapport mensuel",
    aide: "La synthèse d'un mois d'activités, à partir du dernier jour du mois.",
    points: "+75 pour l'encadreur, une fois par mois.",
  },
  bilan: {
    libelle: "Bilan semestriel",
    aide: "Le bilan d'un semestre, à partir de son dernier jour.",
    points: "+200 pour l'encadreur et +100 pour le club, une fois par semestre.",
  },
};

export const ETATS_RAPPORT: Record<RapportResume["etat"], { libelle: string; classe: string }> = {
  brouillon: { libelle: "Brouillon", classe: "bg-mist text-ink" },
  soumis: { libelle: "Soumis", classe: "bg-sky/20 text-logo-blue" },
  a_corriger: { libelle: "À corriger", classe: "bg-sun/40 text-ink" },
  approuve: { libelle: "Approuvé", classe: "bg-leaf/25 text-ink" },
  refuse: { libelle: "Refusé", classe: "bg-logo-red/15 text-logo-red" },
};

export type Champ = {
  cle: string;
  libelle: string;
  long?: boolean;
  obligatoire?: boolean;
  aide?: string;
};

// Les textes de chaque modèle, dans l'ordre du formulaire. Les champs particuliers (date, type, axe, mois,
// semestre, participants, vidéos) sont rendus à part.
export const TEXTES: Record<ModeleRapport, Champ[]> = {
  activite: [
    { cle: "titre", libelle: "Titre", obligatoire: true },
    { cle: "lieu", libelle: "Lieu", obligatoire: true },
    { cle: "responsable", libelle: "Responsable de l'activité", obligatoire: true },
    { cle: "contexte", libelle: "Contexte", long: true },
    { cle: "objectifs", libelle: "Objectifs", long: true, obligatoire: true },
    { cle: "deroulement", libelle: "Déroulement", long: true, obligatoire: true },
    { cle: "resultats", libelle: "Résultats", long: true, obligatoire: true },
    { cle: "difficultes", libelle: "Difficultés", long: true },
    { cle: "recommandations", libelle: "Recommandations", long: true },
  ],
  mensuel: [
    { cle: "titre", libelle: "Titre (facultatif)" },
    { cle: "synthese", libelle: "Synthèse des activités du mois", long: true, obligatoire: true },
    { cle: "analyse", libelle: "Analyse", long: true },
    { cle: "difficultes", libelle: "Difficultés", long: true },
    { cle: "perspectives", libelle: "Perspectives", long: true },
  ],
  bilan: [
    { cle: "titre", libelle: "Titre (facultatif)" },
    { cle: "synthese", libelle: "Synthèse du semestre", long: true, obligatoire: true },
    { cle: "resultats", libelle: "Résultats", long: true, obligatoire: true },
    { cle: "analyse", libelle: "Analyse", long: true },
    { cle: "recommandations", libelle: "Recommandations", long: true },
    { cle: "perspectives", libelle: "Perspectives", long: true },
  ],
};

export const PARTICIPANTS: { cle: string; libelle: string }[] = [
  { cle: "total", libelle: "Participants (total)" },
  { cle: "filles", libelle: "dont filles" },
  { cle: "garcons", libelle: "dont garçons" },
  { cle: "eleves_club", libelle: "dont élèves du club" },
  { cle: "autres", libelle: "dont autres participants" },
];

export const RAPPEL_NOMS =
  "N'écris aucun nom d'élève dans ce rapport : seuls des nombres de participants sont demandés.";

export const octetsLisibles = (octets: number) =>
  octets >= 1024 * 1024
    ? `${(octets / (1024 * 1024)).toFixed(1).replace(".", ",")} Mo`
    : `${Math.max(1, Math.round(octets / 1024))} Ko`;
