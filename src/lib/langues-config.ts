// Langues de l'interface (spec 052, ADR-0015) : la configuration de Paraglide, partagée par Vite et par le script de
// compilation. Sans import de Node ni du navigateur : ce module est lu des deux côtés.

export const LANGUES = ["fr", "en", "de"] as const;
export type Langue = (typeof LANGUES)[number];
export const LANGUE_DE_BASE: Langue = "fr";

/**
 * Les pages traduites (spec 052) : toutes celles qu'on ouvre sans être connecté. Syntaxe des motifs d'adresse
 * (`:param`). Une page absente de cette liste reste en français, à la même adresse dans les trois langues.
 */
export const PAGES_TRADUITES = [
  "/",
  "/club-sante",
  "/les-7-axes",
  "/jeux",
  "/certification",
  "/bibliotheque",
  "/galerie",
  "/magazine",
  "/articles",
  "/articles/:adresse",
  "/agenda",
  "/agenda/:id",
  "/carte-des-clubs",
  "/clubs/:id",
  "/hall-of-fame",
  "/temoignages",
  "/charte",
  "/genie-imhotep/description",
  "/genie-imhotep/inscription",
  "/genie-imhotep/palmares",
  "/genie-imhotep/palmares/:edition",
  "/genie-imhotep/hall-of-fame",
  "/genie-imhotep/hall-of-fame/:edition",
  "/inscription",
  "/connexion",
  "/activation",
  "/mot-de-passe-oublie",
  "/mot-de-passe/nouveau",
  "/certificats/:numero",
  "/carte/:code",
] as const;

const prefixe = (langue: Langue, page: string) =>
  langue === LANGUE_DE_BASE ? page : page === "/" ? `/${langue}` : `/${langue}${page}`;

/**
 * Motifs d'adresse de Paraglide. Les pages traduites d'abord, chacune avec son préfixe ; puis toutes les autres
 * pages, sans préfixe et en français d'abord (le premier motif qui correspond donne la langue).
 */
export const MOTIFS_ADRESSES = [
  ...PAGES_TRADUITES.map((page) => ({
    pattern: page,
    localized: LANGUES.filter((l) => l !== LANGUE_DE_BASE)
      .map((l) => [l, prefixe(l, page)] as [Langue, string])
      .concat([[LANGUE_DE_BASE, page]]),
  })),
  {
    pattern: "/:chemin(.*)?",
    localized: LANGUES.map((l) => [l, "/:chemin(.*)?"] as [Langue, string]).sort(([a]) =>
      a === LANGUE_DE_BASE ? -1 : 1,
    ),
  },
];

/** Options de compilation de Paraglide : langue lue dans l'adresse seulement, sinon le français (pas de cookie). */
export const OPTIONS_PARAGLIDE = {
  project: "./project.inlang",
  outdir: "./src/paraglide",
  strategy: ["url", "baseLocale"] as ("url" | "baseLocale")[],
  urlPatterns: MOTIFS_ADRESSES,
  emitTsDeclarations: true,
};
