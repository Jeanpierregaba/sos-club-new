import {
  BookOpen,
  ClipboardList,
  GraduationCap,
  Image as ImageIcon,
  Newspaper,
  type LucideIcon,
} from "lucide-react";

import type { CategorieRessource, RessourceEntree } from "@/lib/api/client";
import { auSingulier, formatDeLaLangue } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

// Libellés, icône et couleur de couverture de chaque catégorie (spec 028) : le visuel d'une ressource sans
// image de couverture. Les libellés sont lus à l'affichage, dans la langue de la page (spec 052).
const categorie = (
  pluriel: () => string,
  un: () => string,
  icone: LucideIcon,
  fond: string,
): { readonly pluriel: string; readonly un: string; icone: LucideIcon; fond: string } => ({
  get pluriel() {
    return pluriel();
  },
  get un() {
    return un();
  },
  icone,
  fond,
});

export const CATEGORIES: Record<
  CategorieRessource,
  { readonly pluriel: string; readonly un: string; icone: LucideIcon; fond: string }
> = {
  magazine: categorie(m.biblio_cat_magazines, m.biblio_cat_magazine, Newspaper, "bg-grape"),
  guide: categorie(m.biblio_cat_guides, m.biblio_cat_guide, BookOpen, "bg-logo-blue"),
  fiche: categorie(m.biblio_cat_fiches, m.biblio_cat_fiche, ClipboardList, "bg-primary"),
  affiche: categorie(m.biblio_cat_affiches, m.biblio_cat_affiche, ImageIcon, "bg-rose"),
  fascicule: categorie(
    m.biblio_cat_fascicules,
    m.biblio_cat_fascicule,
    GraduationCap,
    "bg-tangerine",
  ),
};

export const ORDRE_CATEGORIES = Object.keys(CATEGORIES) as CategorieRessource[];

export const estCategorie = (valeur: unknown): valeur is CategorieRessource =>
  typeof valeur === "string" && Object.hasOwn(CATEGORIES, valeur);

// 4 404 019 octets → « 4,2 Mo » ; 512 000 → « 500 Ko ».
export function tailleLisible(octets: number): string {
  if (octets < 1024 * 1024)
    return m.biblio_ko({ nombre: String(Math.max(1, Math.round(octets / 1024))) });
  const mo = octets / (1024 * 1024);
  return m.biblio_mo({
    nombre: mo.toLocaleString(formatDeLaLangue(), { maximumFractionDigits: 1 }),
  });
}

// 1 → « 1 page » ; 12 → « 12 pages ».
export const pages = (nombre: number) =>
  (auSingulier(nombre) ? m.biblio_page : m.biblio_pages)({ nombre: String(nombre) });

// 1 → « 1 téléchargement » ; 1234 → « 1 234 téléchargements ».
export function telechargements(nombre: number): string {
  return (auSingulier(nombre) ? m.biblio_un_telechargement : m.biblio_n_telechargements)({
    nombre: nombre.toLocaleString(formatDeLaLangue()),
  });
}

// Une nouvelle ressource, avant saisie.
export const entreeVide: RessourceEntree = {
  titre: "",
  description: "",
  categorie: "guide",
  axe_code: null,
  parution: null,
};
