// Langues de l'interface (spec 052, ADR-0015). La langue vient de l'adresse : `/en/...`, `/de/...`, sinon le
// français. Seules les pages publiques sont traduites ; les autres restent en français, à la même adresse.
import { deLocalizeUrl, getLocale, localizeHref, localizeUrl } from "@/paraglide/runtime.js";

import { LANGUE_DE_BASE, LANGUES, PAGES_TRADUITES, type Langue } from "./langues-config";

export { LANGUES, LANGUE_DE_BASE, type Langue };

/** Réécriture des adresses du routeur : `/en/jeux` est la page `/jeux` en anglais ; chaque lien reprend le préfixe. */
export const REECRITURE_LANGUES = {
  input: ({ url }: { url: URL }) => deLocalizeUrl(url),
  output: ({ url }: { url: URL }) => localizeUrl(url),
};

/** La langue de la page en cours (lue dans l'adresse, pendant le rendu serveur comme dans le navigateur). */
export const langueCourante = (): Langue => getLocale() as Langue;

const PREFIXE = /^\/(fr|en|de)(\/.*)?$/;

/** La langue annoncée par le préfixe d'une adresse brute, même pour une page inconnue (sa 404 suit le préfixe). */
export function langueDeLAdresse(chemin: string): Langue {
  const langue = PREFIXE.exec(chemin)?.[1];
  return langue === "en" || langue === "de" ? langue : LANGUE_DE_BASE;
}

/** L'adresse sans son préfixe de langue. */
export function pageSansLangue(chemin: string): string {
  const trouve = PREFIXE.exec(chemin);
  return trouve ? "/" + (trouve[2] ?? "").replace(/^\/+/, "") : chemin;
}

/**
 * `/en/jeux/` ou `/de/` : l'adresse sans la barre finale, que Paraglide ne reconnaîtrait pas (la page serait une
 * 404). `null` pour toute autre adresse : le français accepte déjà la barre finale.
 */
export function sansBarreFinale(chemin: string): string | null {
  const trouve = /^\/(en|de)(\/.*?)?\/+$/.exec(chemin);
  if (!trouve) return null;
  return `/${trouve[1]}${(trouve[2] ?? "").replace(/^\/+/, "/")}`;
}

const MOTIFS_TRADUITS = PAGES_TRADUITES.map(
  (page) => new RegExp(`^${page.replace(/:[a-z]+/g, "[^/]+")}/?$`),
);

/** La page (adresse sans préfixe) a-t-elle une version anglaise et allemande ? */
export const estTraduite = (page: string): boolean =>
  MOTIFS_TRADUITS.some((motif) => motif.test(page));

/** Un lien interne dans la langue voulue : préfixé pour une page traduite, inchangé sinon. */
export const localiser = (lien: string, langue: Langue): string =>
  localizeHref(lien, { locale: langue });

/** Un lien interne dans la langue de la page en cours ; les ancres, liens externes, `mailto:` et `tel:` inchangés. */
export const lien = (href: string): string =>
  href.startsWith("/") && !href.startsWith("//") ? localiser(href, langueCourante()) : href;

/**
 * L'adresse où renvoyer, s'il le faut : `/fr/...` vers l'adresse sans préfixe (une seule adresse par page), et
 * `/en/...` ou `/de/...` d'une page non traduite vers sa version française. `null` sinon, page inconnue comprise
 * (sa 404 s'affiche dans la langue du préfixe).
 */
export function redirectionLangue(
  chemin: string,
  pageExiste: (page: string) => boolean,
): string | null {
  const trouve = PREFIXE.exec(chemin);
  if (!trouve) return null;
  // Plusieurs barres d'affilée (`/fr//site.com`) n'en font qu'une : jamais d'adresse vers un autre site.
  const page = pageSansLangue(chemin);
  if (trouve[1] === LANGUE_DE_BASE) return page;
  return estTraduite(page) || !pageExiste(page) ? null : page;
}

/**
 * Le routeur a-t-il une page à cette adresse ? Il rapproche `/jeux/xyz` de `/jeux` en gardant le reste dans `**` :
 * ce n'est pas une page qui existe.
 */
export function pageDuRouteur(
  routeur: {
    getMatchedRoutes: (chemin: string) => readonly [unknown, Record<string, string>, unknown];
  },
  chemin: string,
): boolean {
  const [, parametres, route] = routeur.getMatchedRoutes(chemin);
  return route !== undefined && !parametres["**"];
}

/**
 * Les versions d'une page traduite dans chaque langue, pour les moteurs de recherche (`hreflang`). Adresses
 * complètes : les moteurs ignorent les adresses relatives.
 */
export function liensHreflang(
  page: string,
  recherche: string,
  origine: string,
): { hreflang: string; href: string }[] {
  if (!estTraduite(page)) return [];
  const francais = page + recherche;
  return [
    ...LANGUES.map((langue) => ({
      hreflang: langue,
      href: origine + localiser(francais, langue),
    })),
    { hreflang: "x-default", href: origine + francais },
  ];
}

/** Un rang écrit en toutes lettres pour les lecteurs d'écran : « 1er », « 2nd »… selon la langue. */
export function ordinal(rang: number, langue: Langue = langueCourante()): string {
  if (langue === "de") return `${rang}.`;
  if (langue === "en") {
    const fin =
      rang % 100 >= 11 && rang % 100 <= 13 ? "th" : (["th", "st", "nd", "rd"][rang % 10] ?? "th");
    return `${rang}${fin}`;
  }
  return `${rang}${rang === 1 ? "er" : "e"}`;
}

const FORMATS: Record<Langue, string> = { fr: "fr-FR", en: "en-US", de: "de-DE" };

/** Le format des dates et des nombres de la langue en cours. */
export const formatDeLaLangue = (langue: Langue = langueCourante()): string => FORMATS[langue];

/** Les libellés du sélecteur de langue, chacun dans sa propre langue. */
export const NOMS_DES_LANGUES: Record<Langue, { court: string; nom: string }> = {
  fr: { court: "FR", nom: "Français" },
  en: { court: "EN", nom: "English" },
  de: { court: "DE", nom: "Deutsch" },
};

/** Vrai quand la langue met ce nombre au singulier : 0 et 1 en français, 1 seulement en anglais et en allemand. */
export const auSingulier = (nombre: number, langue: Langue = langueCourante()): boolean =>
  new Intl.PluralRules(FORMATS[langue]).select(nombre) === "one";
