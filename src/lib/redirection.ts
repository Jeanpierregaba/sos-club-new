const BASE = "http://site.invalid";
export const PAGE_APRES_CONNEXION = "/mon-espace";

// Renvoie une page du site, jamais une autre adresse : le paramètre vient de l'URL, n'importe qui peut l'écrire.
export function cheminSur(valeur: unknown): string {
  if (typeof valeur !== "string" || !valeur.startsWith("/")) return PAGE_APRES_CONNEXION;
  try {
    const url = new URL(valeur, BASE);
    const chemin = url.pathname + url.search + url.hash;
    const valide =
      url.origin === BASE && !chemin.startsWith("//") && !url.pathname.startsWith("/connexion");
    return valide ? chemin : PAGE_APRES_CONNEXION;
  } catch {
    return PAGE_APRES_CONNEXION;
  }
}
