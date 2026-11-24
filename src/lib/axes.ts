import { m } from "@/paraglide/messages.js";
import mascotteImhotep from "@/assets/mascotte-imhotep.webp";
import mascotteValeurs from "@/assets/mascotte-valeurs.webp";
import mascotteMedias from "@/assets/mascotte-medias.webp";
import mascotteSecourisme from "@/assets/mascotte-secourisme.webp";
import mascotteBourses from "@/assets/mascotte-bourses.webp";
import mascotteLeadership from "@/assets/mascotte-leadership.webp";
import mascotteEnvironnement from "@/assets/mascotte-environnement.webp";

// Les 7 axes d'intervention, en version courte (galerie, quiz « Quel axe est fait pour toi ? »).
// Le détail de chaque axe (activités, textes) est sur la page /les-7-axes, ancre #axe-<n>.
// `couleur` : la couleur de l'axe ; `encre` : la couleur du texte posé dessus.
export const axes = [
  {
    n: 1,
    nom: "Génie Imhotep",
    slogan: "Génie Imhotep, c’est ici et maintenant",
    couleur: "var(--sky)",
    encre: "text-white",
    img: mascotteImhotep,
  },
  {
    n: 2,
    nom: "Santé sexuelle & EVSS",
    slogan: "Un élève bien informé est un élève serein et engagé dans sa communauté",
    couleur: "var(--rose)",
    encre: "text-white",
    img: mascotteValeurs,
  },
  {
    n: 3,
    nom: "Production TV & médias",
    slogan: "La voix des jeunes au cœur des ondes de santé",
    couleur: "var(--grape)",
    encre: "text-white",
    img: mascotteMedias,
  },
  {
    n: 4,
    nom: "Sport & secourisme",
    slogan: "Un esprit sain dans un corps sain et agile",
    couleur: "var(--tangerine)",
    encre: "text-white",
    img: mascotteSecourisme,
  },
  {
    n: 5,
    nom: "Bourses & excellence",
    slogan: "L’excellence récompensée, l’émulation stimulée",
    couleur: "var(--sun)",
    encre: "text-ink",
    img: mascotteBourses,
  },
  {
    n: 6,
    nom: "Leadership & mentorat",
    slogan: "Oser grandir, inspirer et diriger avec intégrité",
    couleur: "var(--bark)",
    encre: "text-white",
    img: mascotteLeadership,
  },
  {
    n: 7,
    nom: "Santé & environnement",
    slogan: "Un environnement scolaire sain pour une jeunesse épanouie",
    couleur: "var(--leaf)",
    encre: "text-white",
    img: mascotteEnvironnement,
  },
] as const;

export type NumeroAxe = (typeof axes)[number]["n"];

// Les titres officiels des 7 axes, dans l'ordre : la page d'accueil et la page « Les 7 axes » les partagent.
export const TITRES_AXES = [
  "Académie GENIE IMHOTEP : jeu de culture générale en santé publique dans les collèges et lycées du Togo",
  "Sensibilisation, Information et Communication sur l’éducation aux valeurs et à la santé sexuelle (EVSS), les Journées Mondiales en lien avec la Santé (JMS)",
  "Production et diffusion des émissions de santé par les élèves sur SOS DOCTEUR TV",
  "Organisation et soutien des activités sportives, culturelles et de secourisme dans les établissements scolaires",
  "Bourses d’excellence, gamification, parrainage des orphelins et distinctions des meilleurs acteurs",
  "Développement personnel, leadership transformationnel, promotion du genre et mentorat",
  "Promotion de la santé, cadre de vie et cohésion sociale (Santé environnementale, nutrition & PEVPAH)",
] as const;

// Les textes d'un axe dans la langue de la page (spec 052). Une fonction, jamais une constante : la langue n'est
// connue qu'au rendu.
export function texteAxe(n: NumeroAxe): { nom: string; slogan: string; titre: string } {
  const cle = (champ: string) => m[`axe_${n}_${champ}` as keyof typeof m] as () => string;
  return { nom: cle("nom")(), slogan: cle("slogan")(), titre: cle("titre")() };
}
