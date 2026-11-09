import {
  BookOpen,
  ClipboardList,
  GraduationCap,
  Image as ImageIcon,
  Newspaper,
  type LucideIcon,
} from "lucide-react";

import type { CategorieRessource, RessourceEntree } from "@/lib/api/client";

// Libellés, icône et couleur de couverture de chaque catégorie (spec 028) : le visuel d'une ressource sans
// image de couverture.
export const CATEGORIES: Record<
  CategorieRessource,
  { pluriel: string; un: string; icone: LucideIcon; fond: string }
> = {
  magazine: { pluriel: "Magazines", un: "Magazine", icone: Newspaper, fond: "bg-grape" },
  guide: {
    pluriel: "Guides d’action",
    un: "Guide d’action",
    icone: BookOpen,
    fond: "bg-logo-blue",
  },
  fiche: {
    pluriel: "Fiches pratiques",
    un: "Fiche pratique",
    icone: ClipboardList,
    fond: "bg-primary",
  },
  affiche: { pluriel: "Affiches", un: "Affiche", icone: ImageIcon, fond: "bg-rose" },
  fascicule: { pluriel: "Fascicules", un: "Fascicule", icone: GraduationCap, fond: "bg-tangerine" },
};

export const ORDRE_CATEGORIES = Object.keys(CATEGORIES) as CategorieRessource[];

export const estCategorie = (valeur: unknown): valeur is CategorieRessource =>
  typeof valeur === "string" && valeur in CATEGORIES;

// 4 404 019 octets → « 4,2 Mo » ; 512 000 → « 500 Ko ».
export function tailleLisible(octets: number): string {
  if (octets < 1024 * 1024) return `${Math.max(1, Math.round(octets / 1024))} Ko`;
  const mo = octets / (1024 * 1024);
  return `${mo.toLocaleString("fr-FR", { maximumFractionDigits: 1 })} Mo`;
}

// 1 → « 1 téléchargement » ; 1234 → « 1 234 téléchargements ».
export function telechargements(nombre: number): string {
  return `${nombre.toLocaleString("fr-FR")} téléchargement${nombre > 1 ? "s" : ""}`;
}

// Une nouvelle ressource, avant saisie.
export const entreeVide: RessourceEntree = {
  titre: "",
  description: "",
  categorie: "guide",
  axe_code: null,
  parution: null,
};
