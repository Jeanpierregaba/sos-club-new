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
