import dimensions from "@/assets/galerie/dimensions.json";
import { axes, type NumeroAxe } from "@/lib/axes";
import { m } from "@/paraglide/messages.js";

export { axes, type NumeroAxe };

// Photos de la galerie, rangées par axe d'intervention (page /les-7-axes) dans `src/assets/galerie/axe-<n>/`, plus
// celles de la coordination nationale. Converties en WebP (1 400 px au plus, sans métadonnées) ; leurs dimensions
// sont dans `dimensions.json`. L'accueil montre les 6 premières (la sélection `A_LA_UNE`), la page /galerie toutes.
export type Categorie = NumeroAxe | "coordination";

export type Photo = {
  categorie: Categorie;
  img: string;
  w: number;
  h: number;
  // La partie de la photo gardée quand elle est rognée dans une vignette.
  pos: string;
  // Lu à l'affichage, dans la langue de la page (spec 052).
  readonly alt: string;
};

export const coordination = () => m.galerie_coordination();

// Ce que montrent les photos de chaque catégorie : le texte alternatif, suivi du numéro de la photo.
const LEGENDES: Record<string, () => string> = {
  "axe-1": m.galerie_legende_1,
  "axe-2": m.galerie_legende_2,
  "axe-3": m.galerie_legende_3,
  "axe-4": m.galerie_legende_4,
  "axe-5": m.galerie_legende_5,
  "axe-6": m.galerie_legende_6,
  "axe-7": m.galerie_legende_7,
  coordination: m.galerie_legende_coordination,
};

const fichiers = import.meta.glob<string>("@/assets/galerie/*/*.webp", {
  eager: true,
  import: "default",
});
const url = (f: string) =>
  Object.entries(fichiers).find(([chemin]) => chemin.endsWith(`/galerie/${f}`))?.[1];

const toutes: Photo[] = dimensions.flatMap(({ f, w, h }) => {
  const img = url(f);
  const [dossier = "", nom = ""] = f.split("/");
  if (!img) return [];
  const categorie: Categorie =
    dossier === "coordination" ? "coordination" : (Number(dossier.slice(4)) as NumeroAxe);
  const numero = Number(nom.replace(/\D+/g, " ").trim().split(" ").pop());
  const legende = LEGENDES[dossier] ?? (() => "");
  return [
    {
      categorie,
      img,
      w,
      h,
      pos: "object-center",
      get alt() {
        return m.galerie_photo({ legende: legende(), numero: String(numero) });
      },
    },
  ];
});

const par = (f: string) => toutes.find((p) => p.img === url(f));

// Les photos mises en avant : les 6 de l'accueil, dans cet ordre, puis l'éventail de la bannière.
const A_LA_UNE = [
  "axe-1/axe-1-04.webp",
  "axe-4/axe-4-04.webp",
  "axe-3/axe-3-12.webp",
  "axe-2/axe-2-17.webp",
  "axe-5/axe-5-02.webp",
  "axe-1/axe-1-30.webp",
];
export const eventail = ["axe-1/axe-1-09.webp", "axe-4/axe-4-06.webp", "axe-2/axe-2-05.webp"]
  .map(par)
  .filter((p): p is Photo => p !== undefined);

const une = A_LA_UNE.map(par).filter((p): p is Photo => p !== undefined);
export const photos: Photo[] = [...une, ...toutes.filter((p) => !une.includes(p))];
