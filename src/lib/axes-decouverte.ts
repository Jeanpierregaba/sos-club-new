import { axes, type NumeroAxe } from "@/lib/axes";
import type { CodeAxe } from "@/lib/api/client";

// Les résultats du jeu « Quel axe est fait pour toi ? » (spec 021), repris du document fonctionnel « Jeu de
// découverte des 7 axes ». L'API calcule le code de l'axe ; le site l'affiche avec la couleur et la mascotte
// officielles de l'axe (`axes`).
type TexteResultat = { n: NumeroAxe; nom: string; titre: string; texte: string; force: string };

const TEXTES: Record<CodeAxe, TexteResultat> = {
  GI: {
    n: 1,
    nom: "Académie Génie Imhotep",
    titre: "Tu es un explorateur du savoir !",
    texte:
      "Curieux et passionné de découvertes, tu aimes apprendre, comprendre et relever des défis intellectuels. Avec l’Académie Génie Imhotep, mets tes connaissances à l’épreuve et découvre de nouvelles façons d’apprendre la santé.",
    force: "La curiosité",
  },
  EVSS: {
    n: 2,
    nom: "Éducation aux Valeurs et à la Santé Sexuelle",
    titre: "Tu es une voix qui fait la différence !",
    texte:
      "Tu aimes défendre tes idées, sensibiliser et encourager les autres à faire des choix responsables. Dans cet axe, tu peux participer à des campagnes de sensibilisation et contribuer à promouvoir le respect, les valeurs et la santé sexuelle.",
    force: "La conviction",
  },
  TV: {
    n: 3,
    nom: "Production TV & Médias",
    titre: "Tu es un créatif dans l’âme !",
    texte:
      "Tu as des idées plein la tête et tu aimes raconter des histoires, filmer, interviewer ou communiquer. Dans cet axe, prends la caméra, exprime-toi et fais découvrir les initiatives des jeunes de ton établissement.",
    force: "La créativité",
  },
  SS: {
    n: 4,
    nom: "Sports & Secourisme",
    titre: "Tu es toujours prêt à passer à l’action !",
    texte:
      "Dynamique et volontaire, tu aimes les activités physiques, l’esprit d’équipe et les défis. Avec cet axe, découvre le sport, apprends les gestes de premiers secours et développe ton sens de l’entraide.",
    force: "L’énergie",
  },
  GB: {
    n: 5,
    nom: "Gamification & Bourses",
    titre: "Tu es un champion des défis !",
    texte:
      "Tu aimes jouer, te dépasser et mesurer tes progrès. Les concours, les challenges et les récompenses te motivent à donner le meilleur de toi-même. Dans cet axe, chaque défi devient une occasion d’apprendre et de progresser.",
    force: "La détermination",
  },
  LM: {
    n: 6,
    nom: "Leadership & Masculinité positive",
    titre: "Tu as l’âme d’un leader !",
    texte:
      "Tu aimes prendre des initiatives, rassembler les autres et transformer les idées en actions. Dans cet axe, apprends à inspirer, à écouter et à exercer un leadership respectueux et responsable.",
    force: "L’initiative",
  },
  SE: {
    n: 7,
    nom: "Santé mentale & Environnement",
    titre: "Tu es un gardien du bien-être !",
    texte:
      "Tu es sensible au bien-être des autres et à la protection de ton environnement. Tu aimes écouter, prendre soin et agir pour un cadre de vie plus sain. Cet axe t’invite à construire un environnement scolaire où chacun peut s’épanouir.",
    force: "L’attention aux autres",
  },
};

export function axeDecouverte(code: CodeAxe) {
  const texte = TEXTES[code];
  const axe = axes.find((a) => a.n === texte.n)!;
  return { ...texte, code, couleur: axe.couleur, encre: axe.encre, img: axe.img };
}

export type AxeDecouverte = ReturnType<typeof axeDecouverte>;

// Partage d'un résultat : le nom de l'axe et un lien vers le jeu, jamais de nom, pseudonyme ni contact. Renvoie
// un message à afficher quand le texte a été copié faute de partage natif.
export async function partagerAxe(nom: string): Promise<string | null> {
  const texte = `Mon axe Clubs Santé SOS Docteur TV : ${nom} ! Et toi, quel axe est fait pour toi ?`;
  const url = `${window.location.origin}/#quel-axe`;
  try {
    if (navigator.share) {
      await navigator.share({ title: "Quel axe est fait pour toi ?", text: texte, url });
      return null;
    }
    await navigator.clipboard.writeText(`${texte} ${url}`);
    return "Texte copié : colle-le où tu veux le partager.";
  } catch {
    // Partage annulé : rien à signaler.
    return null;
  }
}
