import story1 from "@/assets/story1.jpg";
import story2 from "@/assets/story2.jpg";
import slideAxes from "@/assets/slide-axes.jpg";
import slideClubs from "@/assets/slide-clubs.webp";
import slideGenie from "@/assets/slide-genie.jpg";
import slideMascottes from "@/assets/slide-mascottes.jpg";
import grandesFinales from "@/assets/agenda-grandes-finales.jpg";
import banniere from "@/assets/club-sante-banniere.jpg";
import campagneHygiene from "@/assets/campagne-hygiene.jpg";
import campagneEcologie from "@/assets/campagne-ecologie.jpg";
import campagneSecourisme from "@/assets/campagne-secourisme.jpg";

// Photos de la galerie. L'accueil montre les 6 premières, la page /galerie les montre toutes.
// `pos` : la partie de la photo gardée quand elle est rognée dans une vignette.
export const themes = [
  "Génie Imhotep",
  "Vie des clubs",
  "Sports & Secourisme",
  "TV & Médias",
  "Campagnes",
] as const;

export type Photo = {
  theme: (typeof themes)[number];
  img: string;
  w: number;
  h: number;
  pos: string;
  alt: string;
};

export const photos: Photo[] = [
  {
    theme: "Vie des clubs",
    img: slideClubs,
    w: 1493,
    h: 1053,
    pos: "object-center",
    alt: "Des élèves en t-shirt Club Santé, affiches en main, saluent un officiel",
  },
  {
    theme: "Génie Imhotep",
    img: slideGenie,
    w: 2000,
    h: 1600,
    pos: "object-[50%_20%]",
    alt: "Trois élèves en polo bleu au pupitre de la compétition Génie Imhotep",
  },
  {
    theme: "Sports & Secourisme",
    img: story1,
    w: 992,
    h: 672,
    pos: "object-center",
    alt: "Une élève s'entraîne au massage cardiaque sur un mannequin",
  },
  {
    theme: "Vie des clubs",
    img: slideAxes,
    w: 2000,
    h: 1228,
    pos: "object-center",
    alt: "Une salle d'élèves en t-shirt vert applaudit debout, sous le drapeau du Togo",
  },
  {
    theme: "TV & Médias",
    img: story2,
    w: 992,
    h: 672,
    pos: "object-center",
    alt: "Une élève en interviewe une autre devant une caméra",
  },
  {
    theme: "Génie Imhotep",
    img: slideMascottes,
    w: 1514,
    h: 1600,
    pos: "object-[50%_25%]",
    alt: "Remise du trophée de champion national Génie Imhotep à une élève en t-shirt orange",
  },
  {
    theme: "Génie Imhotep",
    img: grandesFinales,
    w: 2000,
    h: 963,
    pos: "object-center",
    alt: "Les finalistes du Championnat national Génie Imhotep sur scène, chèques géants en main",
  },
  {
    theme: "Vie des clubs",
    img: banniere,
    w: 2000,
    h: 1160,
    pos: "object-[60%_30%]",
    alt: "Élèves des Clubs Santé en t-shirts colorés, drapeaux du Togo en main",
  },
  {
    theme: "Campagnes",
    img: campagneHygiene,
    w: 544,
    h: 908,
    pos: "object-[50%_30%]",
    alt: "Affiche de campagne : la mascotte rouge se lave les mains avec une élève",
  },
  {
    theme: "Campagnes",
    img: campagneEcologie,
    w: 544,
    h: 908,
    pos: "object-[50%_45%]",
    alt: "Affiche de campagne : la mascotte verte plante un arbre avec un élève",
  },
  {
    theme: "Campagnes",
    img: campagneSecourisme,
    w: 546,
    h: 908,
    pos: "object-[50%_70%]",
    alt: "Affiche de campagne : la mascotte orange pratique un massage cardiaque",
  },
];
