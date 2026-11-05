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
// `axe` : le numéro de l'axe d'intervention (page /les-7-axes) auquel la photo se rattache ; c'est le filtre de la galerie.
// `pos` : la partie de la photo gardée quand elle est rognée dans une vignette.
export const axes = [
  { n: 1, nom: "Génie Imhotep" },
  { n: 2, nom: "Santé sexuelle & EVSS" },
  { n: 3, nom: "Production TV & médias" },
  { n: 4, nom: "Sport & secourisme" },
  { n: 5, nom: "Bourses & excellence" },
  { n: 6, nom: "Leadership & mentorat" },
  { n: 7, nom: "Santé & environnement" },
] as const;

export type NumeroAxe = (typeof axes)[number]["n"];

export type Photo = {
  axe: NumeroAxe;
  img: string;
  w: number;
  h: number;
  pos: string;
  alt: string;
};

export const photos: Photo[] = [
  {
    axe: 2,
    img: slideClubs,
    w: 1493,
    h: 1053,
    pos: "object-center",
    alt: "Des élèves en t-shirt Club Santé, affiches en main, saluent un officiel",
  },
  {
    axe: 1,
    img: slideGenie,
    w: 2000,
    h: 1600,
    pos: "object-[50%_20%]",
    alt: "Trois élèves en polo bleu au pupitre de la compétition Génie Imhotep",
  },
  {
    axe: 4,
    img: story1,
    w: 992,
    h: 672,
    pos: "object-center",
    alt: "Une élève s'entraîne au massage cardiaque sur un mannequin",
  },
  {
    axe: 6,
    img: slideAxes,
    w: 2000,
    h: 1228,
    pos: "object-center",
    alt: "Une salle d'élèves en t-shirt vert applaudit debout, sous le drapeau du Togo",
  },
  {
    axe: 3,
    img: story2,
    w: 992,
    h: 672,
    pos: "object-center",
    alt: "Une élève en interviewe une autre devant une caméra",
  },
  {
    axe: 1,
    img: slideMascottes,
    w: 1514,
    h: 1600,
    pos: "object-[50%_25%]",
    alt: "Remise du trophée de champion national Génie Imhotep à une élève en t-shirt orange",
  },
  {
    axe: 1,
    img: grandesFinales,
    w: 2000,
    h: 963,
    pos: "object-center",
    alt: "Les finalistes du Championnat national Génie Imhotep sur scène, chèques géants en main",
  },
  {
    axe: 6,
    img: banniere,
    w: 2000,
    h: 1160,
    pos: "object-[60%_30%]",
    alt: "Élèves des Clubs Santé en t-shirts colorés, drapeaux du Togo en main",
  },
  {
    axe: 7,
    img: campagneHygiene,
    w: 544,
    h: 908,
    pos: "object-[50%_30%]",
    alt: "Affiche de campagne : la mascotte rouge se lave les mains avec une élève",
  },
  {
    axe: 7,
    img: campagneEcologie,
    w: 544,
    h: 908,
    pos: "object-[50%_45%]",
    alt: "Affiche de campagne : la mascotte verte plante un arbre avec un élève",
  },
  {
    axe: 4,
    img: campagneSecourisme,
    w: 546,
    h: 908,
    pos: "object-[50%_70%]",
    alt: "Affiche de campagne : la mascotte orange pratique un massage cardiaque",
  },
];
