// Suivi d'activité anonyme (spec 051, ADR-0014) : le site envoie à l'API un type d'événement et le gabarit de la
// page, jamais une saisie ni un identifiant. Sans cookie, sans service tiers, et rien si le navigateur demande à ne
// pas être suivi. L'envoi n'attend rien et n'affiche jamais d'erreur : le suivi ne gêne pas la navigation.
import { useEffect, useRef } from "react";

export type TypeEvenement =
  "page_vue" | "clic_inscription" | "etape_inscription" | "recherche" | "erreur";

export type EvenementActivite = {
  type: TypeEvenement;
  chemin: string;
  detail?: string;
  referent?: string;
  utm_source?: string;
  entree?: boolean;
};

const ADRESSE = "/api/activite/evenements";

function nePasSuivre(): boolean {
  const nav = navigator as Navigator & { globalPrivacyControl?: boolean };
  return nav.globalPrivacyControl === true || nav.doNotTrack === "1";
}

export function signaler(evenement: EvenementActivite): void {
  if (typeof window === "undefined" || nePasSuivre()) return;
  const corps = JSON.stringify(evenement);
  try {
    if (navigator.sendBeacon?.(ADRESSE, new Blob([corps], { type: "application/json" }))) return;
  } catch {
    // Repli sur fetch ci-dessous.
  }
  void fetch(ADRESSE, {
    method: "POST",
    body: corps,
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    keepalive: true,
  }).catch(() => undefined);
}

// Clics « S'inscrire » ------------------------------------------------------------------------------------------

const ENDROITS_PAR_PAGE: [RegExp, string][] = [
  [/^\/$/, "accueil"],
  [/^\/jeux/, "jeux"],
  [/^\/quiz/, "quiz"],
  [/^\/certification/, "certification"],
  [/^\/connexion/, "connexion"],
  [/^\/genie-imhotep/, "genie-imhotep"],
  [/^\/club-sante/, "club-sante"],
  [/^\/bibliotheque/, "bibliotheque"],
];

/** L'endroit d'où part un lien d'inscription : le menu, le pied de page, ou la page où il se trouve. */
export function endroitDuClic(lien: Element, page: string): string {
  if (lien.closest("header")) return "menu";
  if (lien.closest("footer")) return "pied-de-page";
  return ENDROITS_PAR_PAGE.find(([motif]) => motif.test(page))?.[1] ?? "autre";
}

/** Le lien d'inscription d'un clic, s'il y en a un : seulement l'inscription au site, pas celle de Génie Imhotep. */
export function lienInscription(cible: EventTarget | null): HTMLAnchorElement | null {
  const lien = cible instanceof Element ? cible.closest("a[href]") : null;
  if (!(lien instanceof HTMLAnchorElement)) return null;
  const url = new URL(lien.href, window.location.href);
  return url.origin === window.location.origin && url.pathname === "/inscription" ? lien : null;
}

// Pages vues ----------------------------------------------------------------------------------------------------

// Pages dont le contenu se compte un par un (l'API refuse les autres détails).
const DETAILS: Record<string, string> = { "/articles/$adresse": "adresse", "/quiz/$id": "id" };

type Correspondance = { fullPath: string; params: Record<string, string> };

/** L'événement d'une page vue, à partir de la dernière route trouvée par le routeur. */
export function pageVue(
  correspondance: Correspondance,
  entree: { referent: string; recherche: string } | null,
): EvenementActivite | null {
  const chemin =
    correspondance.fullPath !== "/" && correspondance.fullPath.endsWith("/")
      ? correspondance.fullPath.slice(0, -1)
      : correspondance.fullPath;
  // Les pages de l'équipe ne sont pas comptées (l'API les ignore de toute façon).
  if (chemin.startsWith("/admin")) return null;
  const evenement: EvenementActivite = { type: "page_vue", chemin };
  const parametre = DETAILS[chemin];
  if (parametre && correspondance.params[parametre]) {
    evenement.detail = correspondance.params[parametre].toLowerCase();
  }
  if (entree) {
    evenement.entree = true;
    if (entree.referent) evenement.referent = entree.referent.slice(0, 500);
    const utm = new URLSearchParams(entree.recherche).get("utm_source");
    if (utm) evenement.utm_source = utm.slice(0, 100);
  }
  return evenement;
}

// Étapes et recherches -------------------------------------------------------------------------------------------

export type ProfilInscription = "eleve" | "encadreur" | "visiteur";

/** « ouvert » à l'affichage du formulaire ; renvoie de quoi signaler « commence » à la première saisie. */
export function useEtapesInscription(profil: ProfilInscription): () => void {
  const commence = useRef(false);
  useEffect(() => {
    signaler({ type: "etape_inscription", chemin: "/inscription", detail: `${profil}:ouvert` });
  }, [profil]);
  return () => {
    if (commence.current) return;
    commence.current = true;
    signaler({ type: "etape_inscription", chemin: "/inscription", detail: `${profil}:commence` });
  };
}

/** Une recherche restée sans résultat une seconde, une fois par texte. Seules l'inscription et la carte des clubs. */
export function useRechercheSansResultat(texte: string, sansResultat: boolean): void {
  const dejaSignales = useRef(new Set<string>());
  useEffect(() => {
    const propre = texte.trim().toLowerCase();
    if (!sansResultat || propre.replace(/\s/g, "").length < 3 || dejaSignales.current.has(propre))
      return;
    const page = window.location.pathname;
    if (page !== "/inscription" && page !== "/carte-des-clubs") return;
    const minuteur = setTimeout(() => {
      dejaSignales.current.add(propre);
      signaler({ type: "recherche", chemin: page, detail: propre.slice(0, 200) });
    }, 1000);
    return () => clearTimeout(minuteur);
  }, [texte, sansResultat]);
}
