// Résultats du 1er Championnat national Génie Imhotep, repris du document « Organisation et résultats
// des compétitions Génie Imhotep à divers niveaux » remis par AIMES-AFRIQUE.
// Les noms sont harmonisés (majuscules, accents, tirets). Au tableau I, le qualifié de Zio est écrit
// « Lycée Davié » : c'est le Lycée Dalavé, inscrit dans cette préfecture et repris aux tableaux II et III.
// Seuls des établissements figurent ici, jamais d'élèves (docs/RULES.md).

export type RegionId =
  "grand-lome" | "maritime" | "plateaux-est" | "plateaux-ouest" | "centrale" | "kara" | "savanes";

export const CHAMPION = "Lycée d’Adétikopé";

// Ordre d'affichage des régions, du sud au nord, comme dans le document.
export const ordreRegions: RegionId[] = [
  "grand-lome",
  "maritime",
  "plateaux-est",
  "plateaux-ouest",
  "centrale",
  "kara",
  "savanes",
];

// Phase préfectorale : une ligne par préfecture (ou zone), les clubs engagés puis le qualifié.
export type Prefectorale = {
  region: RegionId;
  iesg: string;
  prefecture: string;
  clubs: string[];
  qualifie: string;
  note?: string;
};

export const prefectorales: Prefectorale[] = [
  {
    region: "grand-lome",
    iesg: "Golfe",
    prefecture: "Golfe (zone 1)",
    clubs: ["Lycée de Tokoin 1", "Complexe Saint-Joseph", "Lycée Bè-Kpota", "Lycée Gbényédzi-Kopé"],
    qualifie: "Lycée de Tokoin 1",
  },
  {
    region: "grand-lome",
    iesg: "Golfe",
    prefecture: "Golfe (zone 2)",
    clubs: ["Lycée de Tokoin 2", "Complexe NDA", "Lycée Nyékonakpoè", "Lycée Kodjoviakopé"],
    qualifie: "Lycée de Tokoin 2",
  },
  {
    region: "grand-lome",
    iesg: "Golfe",
    prefecture: "Golfe (zone 3)",
    clubs: ["Protestant Tokoin", "Lycée Adidogomé 1", "Lycée Avédji", "CPL NEEA"],
    qualifie: "Lycée Adidogomé 1",
  },
  {
    region: "grand-lome",
    iesg: "Agoè",
    prefecture: "Agoè (zone 1)",
    clubs: ["Lycée Agoè Centre", "Lycée Zanguéra"],
    qualifie: "Lycée Agoè Centre",
  },
  {
    region: "grand-lome",
    iesg: "Agoè",
    prefecture: "Agoè (zone 2)",
    clubs: [CHAMPION, "CSI Zongo"],
    qualifie: CHAMPION,
  },
  {
    region: "maritime",
    iesg: "Tsévié",
    prefecture: "Avé",
    clubs: ["Lycée Attidjin", "Lycée Badja", "Lycée Assahoun", "Lycée Noépé"],
    qualifie: "Lycée Noépé",
  },
  {
    region: "maritime",
    iesg: "Tsévié",
    prefecture: "Zio",
    clubs: ["Lycée Djagblé", "Lycée Dalavé", "Lycée Tsévié 1", "Lycée Agbélouvé"],
    qualifie: "Lycée Dalavé",
  },
  {
    region: "maritime",
    iesg: "Vogan",
    prefecture: "Vo",
    clubs: ["Lycée Hahotoé", "Lycée Vogan 1", "Lycée Dzrékpo", "Lycée Dagbati"],
    qualifie: "Lycée Vogan 1",
  },
  {
    region: "maritime",
    iesg: "Vogan",
    prefecture: "Yoto",
    clubs: ["Lycée Ahépé", "Lycée Tchékpo", "Lycée Tabligbo", "Lycée Kini-Kondji"],
    qualifie: "Lycée Tchékpo",
  },
  {
    region: "maritime",
    iesg: "Aného",
    prefecture: "Lacs",
    clubs: ["Lycée Zébévi", "Lycée Gbodjomé", "Lycée Aného Ville", "Lycée Aklakou"],
    qualifie: "Lycée Zébévi",
  },
  {
    region: "maritime",
    iesg: "Aného",
    prefecture: "Bas-Mono",
    clubs: ["Lycée Attitogon", "Lycée Afagnan Ville", "Lycée Masséda", "Lycée Afagnan Gbléta"],
    qualifie: "Lycée Attitogon",
  },
  {
    region: "plateaux-est",
    iesg: "Anié",
    prefecture: "Anié",
    clubs: ["Lycée Anié-Est", "Lycée moderne d’Anié", "Lycée Anié 2", "Lycée Adobenou"],
    qualifie: "Lycée moderne d’Anié",
  },
  {
    region: "plateaux-est",
    iesg: "Anié",
    prefecture: "Est-Mono",
    clubs: ["Lycée Morétan", "Lycée Izati", "Lycée Nymassila", "Lycée Elavagnon"],
    qualifie: "Lycée Morétan",
  },
  {
    region: "plateaux-est",
    iesg: "Atakpamé",
    prefecture: "Ogou",
    clubs: ["Lycée d’Atakpamé", "Lycée Agbonou", "Lycée Afeyékpota", "Collège NDA"],
    qualifie: "Lycée d’Atakpamé",
  },
  {
    region: "plateaux-est",
    iesg: "Atakpamé",
    prefecture: "Amou",
    clubs: ["Lycée Témédja", "Lycée Amlamé", "Lycée Amou-Oblo", "Lycée Koutoukpa"],
    qualifie: "Lycée Témédja",
  },
  {
    region: "plateaux-est",
    iesg: "Notsé",
    prefecture: "Haho",
    clubs: ["Lycée Notsé", "Lycée Wahala", "Lycée Asrama", "Collège NDA Notsé"],
    qualifie: "Lycée Wahala",
  },
  {
    region: "plateaux-est",
    iesg: "Notsé",
    prefecture: "Moyen-Mono",
    clubs: ["Lycée de Tado", "Lycée Tohoun", "Lycée Kpékplémé"],
    qualifie: "Lycée de Tado",
  },
  {
    region: "plateaux-ouest",
    iesg: "Kpalimé",
    prefecture: "Kloto",
    clubs: ["Lycée 30 Août", "Lycée de Kpodzi", "Lycée Kpéta", "Lycée Nyivémé", "Lycée de Lavié"],
    qualifie: "Lycée 30 Août",
  },
  {
    region: "plateaux-ouest",
    iesg: "Kpalimé",
    prefecture: "Agou",
    clubs: [
      "Lycée Agou",
      "Lycée Avétonou",
      "Lycée des 2 Nyogbo",
      "Lycée Kati",
      "Lycée Amoussoukopé",
    ],
    qualifie: "Lycée Avétonou",
  },
  {
    region: "plateaux-ouest",
    iesg: "Badou",
    prefecture: "Wawa",
    clubs: ["Lycée Badou", "Lycée Klabè-Efoukpa", "Lycée Okou", "Lycée Tomégbé"],
    qualifie: "Lycée Klabè-Efoukpa",
  },
  {
    region: "plateaux-ouest",
    iesg: "Badou",
    prefecture: "Akébou",
    clubs: ["Lycée Kougnohou"],
    qualifie: "Lycée Kougnohou",
    note: "Seul établissement engagé dans l’Akébou.",
  },
  {
    region: "plateaux-ouest",
    iesg: "Adéta",
    prefecture: "Kpélé",
    clubs: ["Lycée Adéta", "Lycée Akata", "Lycée Goudévé", "Lycée Kpélé-Elé"],
    qualifie: "Lycée Kpélé-Elé",
  },
  {
    region: "plateaux-ouest",
    iesg: "Adéta",
    prefecture: "Danyi",
    clubs: [
      "Lycée Danyi Apéyémé",
      "Lycée Danyi Elavagno",
      "Lycée Danyi Kudzragan",
      "Collège Saint-Michel",
    ],
    qualifie: "Lycée Danyi Elavagno",
  },
  {
    region: "centrale",
    iesg: "Sotouboua",
    prefecture: "Mô",
    clubs: ["Lycée Djarkpanga", "Lycée Tindjassi"],
    qualifie: "Lycée Djarkpanga",
    note: "Victoire sur tapis vert : le Lycée Tindjassi ne s’est pas déplacé.",
  },
  {
    region: "centrale",
    iesg: "Sotouboua",
    prefecture: "Sotouboua",
    clubs: [
      "Lycée Sotouboua Ville 1",
      "Lycée Sotouboua Ville 2",
      "Lycée scientifique Robert Mattle",
      "CPC NDPAIX",
    ],
    qualifie: "CPC NDPAIX",
  },
  {
    region: "centrale",
    iesg: "Sotouboua",
    prefecture: "Blitta",
    clubs: ["Lycée Blitta Gare", "Lycée Blitta Carrefour", "Lycée Langabou", "Lycée Yaloubé"],
    qualifie: "Lycée Blitta Gare",
  },
  {
    region: "centrale",
    iesg: "Sokodé",
    prefecture: "Tchaoudjo",
    clubs: ["Lycée moderne de Sokodé", "Lycée Kpangalam", "Lycée Sainte-Marie", "Lycée Bamabodolo"],
    qualifie: "Lycée moderne de Sokodé",
  },
  {
    region: "centrale",
    iesg: "Sokodé",
    prefecture: "Tchamba",
    clubs: ["Lycée Tchamba", "Lycée Tchamba Ville"],
    qualifie: "Lycée Tchamba",
  },
  {
    region: "kara",
    iesg: "Bassar",
    prefecture: "Bassar",
    clubs: ["Lycée Bassar", "Lycée Binaparba", "Lycée Kabou", "Lycée Sanda Kagbanda"],
    qualifie: "Lycée Binaparba",
  },
  {
    region: "kara",
    iesg: "Bassar",
    prefecture: "Dankpen",
    clubs: ["Lycée Guérin-Kouka 1", "Lycée Guérin-Kouka 2", "Lycée Namon", "Lycée Kidjaboun"],
    qualifie: "Lycée Guérin-Kouka 1",
  },
  {
    region: "kara",
    iesg: "Kara",
    prefecture: "Kozah",
    clubs: ["Lycée scientifique de Kara", "Lycée Kara 1", "Lycée Yadè Sodè", "Lycée Lama-Kpédah"],
    qualifie: "Lycée scientifique de Kara",
  },
  {
    region: "kara",
    iesg: "Kara",
    prefecture: "Binah",
    clubs: ["Lycée Kémérida", "Lycée Pagouda", "Lycée Kétao", "Lycée Pessaré"],
    qualifie: "Lycée Kémérida",
  },
  {
    region: "kara",
    iesg: "Kara",
    prefecture: "Assoli",
    clubs: ["Lycée Bafilo", "Lycée Koumondè", "Lycée Soudou", "CSI El Houda"],
    qualifie: "Lycée Bafilo",
  },
  {
    region: "kara",
    iesg: "Niamtougou",
    prefecture: "Doufelgou",
    clubs: ["Lycée Niamtougou", "Lycée Marie Romano", "Lycée Baga", "Lycée Siou"],
    qualifie: "Lycée Marie Romano",
  },
  {
    region: "kara",
    iesg: "Niamtougou",
    prefecture: "Kéran",
    clubs: ["Lycée Kantè 1", "Lycée Kantè 2", "Lycée Atalotè", "Lycée Pessidè"],
    qualifie: "Lycée Kantè 1",
  },
  {
    region: "savanes",
    iesg: "Mango",
    prefecture: "Oti",
    clubs: ["Lycée Mango", "Lycée Barkoissi", "CPL Millenium", "CPC Mgr Hanrion"],
    qualifie: "Lycée Mango",
  },
  {
    region: "savanes",
    iesg: "Mango",
    prefecture: "Oti-Sud",
    clubs: ["Lycée Takpamba", "Lycée Mogou", "Lycée Koumongou", "Lycée Gando"],
    qualifie: "Lycée Gando",
  },
  {
    region: "savanes",
    iesg: "Mango",
    prefecture: "Kpendjal",
    clubs: ["Lycée Borgou", "Lycée Mandouri", "Lycée Koundjouré"],
    qualifie: "Lycée Mandouri",
  },
  {
    region: "savanes",
    iesg: "Mango",
    prefecture: "Kpendjal-Ouest",
    clubs: ["Lycée Ogaro", "Lycée Naki-Est", "Lycée Tambonga", "Lycée Papri"],
    qualifie: "Lycée Naki-Est",
  },
  {
    region: "savanes",
    iesg: "Dapaong",
    prefecture: "Tône",
    clubs: ["Lycée Nassablé", "Lycée Dapaong Ville", "Lycée Kantindi", "CPL Yanfoum"],
    qualifie: "Lycée Nassablé",
  },
  {
    region: "savanes",
    iesg: "Dapaong",
    prefecture: "Tandjouaré",
    clubs: ["Lycée Tandjouaré", "Lycée Nano", "Lycée Bombouaka", "Lycée Moatog"],
    qualifie: "Lycée Nano",
  },
  {
    region: "savanes",
    iesg: "Dapaong",
    prefecture: "Cinkassé",
    clubs: ["Lycée Cinkassé", "Lycée Timbou", "Lycée Nadoundji", "CPC Don Bosco"],
    qualifie: "Lycée Cinkassé",
  },
];

// Une équipe dans un match ; `pts` manque quand le document ne donne pas le score.
export type Equipe = { nom: string; pts?: number };

// Phase inspectorale : les éventuels matchs éliminatoires, puis la finale de l'inspection.
export type Inspectorale = {
  region: RegionId;
  iesg: string;
  eliminatoires?: string[];
  finale: [Equipe, Equipe];
  gagnant: string;
};

export const inspectorales: Inspectorale[] = [
  {
    region: "grand-lome",
    iesg: "Golfe",
    eliminatoires: [
      "Match G1 : Lycée Adidogomé 1 contre Lycée de Tokoin 2 ; Lycée de Tokoin 1 en réserve.",
    ],
    finale: [
      { nom: "Lycée de Tokoin 2", pts: 480 },
      { nom: "Lycée de Tokoin 1", pts: 480 },
    ],
    gagnant: "Lycée de Tokoin 2",
  },
  {
    region: "grand-lome",
    iesg: "Agoè",
    finale: [
      { nom: "Lycée Agoè Centre", pts: 450 },
      { nom: CHAMPION, pts: 480 },
    ],
    gagnant: CHAMPION,
  },
  {
    region: "maritime",
    iesg: "Tsévié",
    finale: [
      { nom: "Lycée Noépé", pts: 400 },
      { nom: "Lycée Dalavé", pts: 420 },
    ],
    gagnant: "Lycée Dalavé",
  },
  {
    region: "maritime",
    iesg: "Vogan",
    finale: [
      { nom: "Lycée Vogan 1", pts: 220 },
      { nom: "Lycée Tchékpo", pts: 300 },
    ],
    gagnant: "Lycée Tchékpo",
  },
  {
    region: "maritime",
    iesg: "Aného",
    finale: [
      { nom: "Lycée Zébévi", pts: 450 },
      { nom: "Lycée Attitogon", pts: 200 },
    ],
    gagnant: "Lycée Zébévi",
  },
  {
    region: "plateaux-est",
    iesg: "Anié",
    finale: [
      { nom: "Lycée moderne d’Anié", pts: 300 },
      { nom: "Lycée Morétan", pts: 140 },
    ],
    gagnant: "Lycée moderne d’Anié",
  },
  {
    region: "plateaux-est",
    iesg: "Atakpamé",
    finale: [
      { nom: "Lycée d’Atakpamé", pts: 380 },
      { nom: "Lycée Témédja", pts: 350 },
    ],
    gagnant: "Lycée d’Atakpamé",
  },
  {
    region: "plateaux-est",
    iesg: "Notsé",
    finale: [
      { nom: "Lycée Wahala", pts: 300 },
      { nom: "Lycée de Tado", pts: 170 },
    ],
    gagnant: "Lycée Wahala",
  },
  {
    region: "plateaux-ouest",
    iesg: "Kpalimé",
    finale: [
      { nom: "Lycée 30 Août", pts: 190 },
      { nom: "Lycée Avétonou", pts: 350 },
    ],
    gagnant: "Lycée Avétonou",
  },
  {
    region: "plateaux-ouest",
    iesg: "Badou",
    finale: [
      { nom: "Lycée Klabè-Efoukpa", pts: 310 },
      { nom: "Lycée Kougnohou", pts: 170 },
    ],
    gagnant: "Lycée Klabè-Efoukpa",
  },
  {
    region: "plateaux-ouest",
    iesg: "Adéta",
    finale: [
      { nom: "Lycée Kpélé-Elé", pts: 120 },
      { nom: "Lycée Danyi Elavagno", pts: 270 },
    ],
    gagnant: "Lycée Danyi Elavagno",
  },
  {
    region: "centrale",
    iesg: "Sotouboua",
    eliminatoires: [
      "Match S1 : Lycée Blitta Gare contre CPC NDPAIX ; Lycée Blitta Gare en réserve.",
    ],
    finale: [
      { nom: "CPC NDPAIX", pts: 380 },
      { nom: "Lycée Djarkpanga", pts: 70 },
    ],
    gagnant: "CPC NDPAIX",
  },
  {
    region: "centrale",
    iesg: "Sokodé",
    finale: [
      { nom: "Lycée moderne de Sokodé", pts: 320 },
      { nom: "Lycée Tchamba", pts: 320 },
    ],
    gagnant: "Lycée Tchamba",
  },
  {
    region: "kara",
    iesg: "Bassar",
    finale: [
      { nom: "Lycée Binaparba", pts: 310 },
      { nom: "Lycée Guérin-Kouka 1", pts: 290 },
    ],
    gagnant: "Lycée Binaparba",
  },
  {
    region: "kara",
    iesg: "Kara",
    eliminatoires: [
      "Match K1 : Lycée scientifique de Kara contre Lycée Kémérida ; Lycée Bafilo en réserve.",
    ],
    finale: [
      { nom: "Lycée scientifique de Kara", pts: 400 },
      { nom: "Lycée Bafilo", pts: 290 },
    ],
    gagnant: "Lycée scientifique de Kara",
  },
  {
    region: "kara",
    iesg: "Niamtougou",
    finale: [{ nom: "Lycée Marie Romano" }, { nom: "Lycée Kantè 1" }],
    gagnant: "Lycée Marie Romano",
  },
  {
    region: "savanes",
    iesg: "Mango",
    eliminatoires: [
      "Match M1 : Lycée Mango contre Lycée Gando.",
      "Match M2 : Lycée Mandouri contre Lycée Naki-Est.",
    ],
    finale: [
      { nom: "Lycée Mango", pts: 250 },
      { nom: "Lycée Naki-Est", pts: 300 },
    ],
    gagnant: "Lycée Naki-Est",
  },
  {
    region: "savanes",
    iesg: "Dapaong",
    eliminatoires: ["Match D1 : Lycée Nassablé contre Lycée Nano ; Lycée Cinkassé en réserve."],
    finale: [
      { nom: "Lycée Nassablé", pts: 490 },
      { nom: "Lycée Cinkassé", pts: 340 },
    ],
    gagnant: "Lycée Nassablé",
  },
];

// Phase régionale : les champions d'inspection de chaque région, puis le champion régional.
// Le document ne donne pas les scores de cette phase.
export type Regionale = {
  region: RegionId;
  champions: { iesg: string; lycee: string; prefecture: string }[];
  gagnant: string;
};

export const regionales: Regionale[] = [
  {
    region: "grand-lome",
    champions: [
      { iesg: "Golfe", lycee: "Lycée de Tokoin 2", prefecture: "Golfe" },
      { iesg: "Agoè", lycee: CHAMPION, prefecture: "Agoè" },
    ],
    gagnant: CHAMPION,
  },
  {
    region: "maritime",
    champions: [
      { iesg: "Tsévié", lycee: "Lycée Dalavé", prefecture: "Zio" },
      { iesg: "Vogan", lycee: "Lycée Tchékpo", prefecture: "Yoto" },
      { iesg: "Aného", lycee: "Lycée Zébévi", prefecture: "Lacs" },
    ],
    gagnant: "Lycée Dalavé",
  },
  {
    region: "plateaux-est",
    champions: [
      { iesg: "Anié", lycee: "Lycée moderne d’Anié", prefecture: "Anié" },
      { iesg: "Atakpamé", lycee: "Lycée d’Atakpamé", prefecture: "Ogou" },
      { iesg: "Notsé", lycee: "Lycée Wahala", prefecture: "Haho" },
    ],
    gagnant: "Lycée Wahala",
  },
  {
    region: "plateaux-ouest",
    champions: [
      { iesg: "Kpalimé", lycee: "Lycée Avétonou", prefecture: "Agou" },
      { iesg: "Badou", lycee: "Lycée Klabè-Efoukpa", prefecture: "Wawa" },
      { iesg: "Adéta", lycee: "Lycée Danyi Elavagno", prefecture: "Danyi" },
    ],
    gagnant: "Lycée Avétonou",
  },
  {
    region: "centrale",
    champions: [
      { iesg: "Sotouboua", lycee: "CPC NDPAIX", prefecture: "Sotouboua" },
      { iesg: "Sokodé", lycee: "Lycée Tchamba", prefecture: "Tchamba" },
    ],
    gagnant: "Lycée Tchamba",
  },
  {
    region: "kara",
    champions: [
      { iesg: "Bassar", lycee: "Lycée Binaparba", prefecture: "Bassar" },
      { iesg: "Kara", lycee: "Lycée scientifique de Kara", prefecture: "Kozah" },
      { iesg: "Niamtougou", lycee: "Lycée Marie Romano", prefecture: "Doufelgou" },
    ],
    gagnant: "Lycée scientifique de Kara",
  },
  {
    region: "savanes",
    champions: [
      { iesg: "Mango", lycee: "Lycée Naki-Est", prefecture: "Kpendjal-Ouest" },
      { iesg: "Dapaong", lycee: "Lycée Nassablé", prefecture: "Tône" },
    ],
    gagnant: "Lycée Naki-Est",
  },
];

// Phase nationale : les 7 champions régionaux, et le meilleur perdant des quarts pour compléter le tableau.
// `note` : une mention à côté du nom, comme « Meilleur perdant ».
export type EquipeNationale = Equipe & { region: RegionId; note?: string };

export type MatchNational = {
  jeu: number;
  tour: "quart" | "demi" | "finale";
  a: EquipeNationale;
  b: EquipeNationale;
  gagnant: string;
};

export const nationale: MatchNational[] = [
  {
    jeu: 1,
    tour: "quart",
    a: { nom: "Lycée Tchamba", region: "centrale", pts: 610 },
    b: { nom: "Lycée Naki-Est", region: "savanes", pts: 400 },
    gagnant: "Lycée Tchamba",
  },
  {
    jeu: 2,
    tour: "quart",
    a: { nom: "Lycée scientifique de Kara", region: "kara", pts: 550 },
    b: { nom: "Lycée Wahala", region: "plateaux-est", pts: 490 },
    gagnant: "Lycée scientifique de Kara",
  },
  {
    jeu: 3,
    tour: "quart",
    a: { nom: CHAMPION, region: "grand-lome", pts: 610 },
    b: { nom: "Lycée Dalavé", region: "maritime", pts: 450 },
    gagnant: CHAMPION,
  },
  {
    jeu: 4,
    tour: "quart",
    a: { nom: "Lycée Avétonou", region: "plateaux-ouest", pts: 360 },
    b: { nom: "Lycée Wahala", region: "plateaux-est", pts: 350, note: "Meilleur perdant" },
    gagnant: "Lycée Avétonou",
  },
  {
    jeu: 5,
    tour: "demi",
    a: { nom: "Lycée scientifique de Kara", region: "kara", pts: 650 },
    b: { nom: "Lycée Tchamba", region: "centrale", pts: 320 },
    gagnant: "Lycée scientifique de Kara",
  },
  {
    jeu: 6,
    tour: "demi",
    a: { nom: CHAMPION, region: "grand-lome", pts: 680 },
    b: { nom: "Lycée Avétonou", region: "plateaux-ouest", pts: 240 },
    gagnant: CHAMPION,
  },
  {
    jeu: 7,
    tour: "finale",
    a: { nom: CHAMPION, region: "grand-lome", pts: 490 },
    b: { nom: "Lycée scientifique de Kara", region: "kara", pts: 360 },
    gagnant: CHAMPION,
  },
];
