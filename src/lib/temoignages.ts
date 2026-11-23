export type Temoignage = {
  // L'ancre du témoignage sur la page /temoignages.
  id: string;
  // La phrase affichée en grand dans la section de l'accueil ; la suite se lit sur la page /temoignages.
  t: string;
  suite?: string[];
  // Un élève n'apparaît que par son prénom et l'initiale de son nom (docs/RULES.md).
  nom: string;
  role: string;
};

// Témoignages publiés avec l'accord de leurs auteurs.
export const temoignages: Temoignage[] = [
  {
    id: "ayiman-n",
    t: "Depuis mon intégration au Club Santé SOS Dr TV de mon établissement, j'ai beaucoup appris sur la santé, le respect de soi et des autres.",
    suite: [
      "Grâce aux différentes activités de sensibilisation, j'ai acquis des connaissances sur la santé sexuelle et reproductive, les relations interpersonnelles saines, la lutte contre les violences et la prévention des grossesses précoces.",
      "Le Club Santé m'a également permis de développer mon sens des responsabilités, ma confiance en moi et mon esprit d'équipe.",
      "Aujourd'hui, je suis capable de partager les bonnes informations avec mes camarades, mes frères, mes sœurs et même au sein de ma communauté.",
      "Je tiens à remercier tout particulièrement le Docteur KODOM Serge Michel, initiateur des Clubs Santé SOS Dr TV, ainsi que tous les encadreurs, pour leur engagement, leur accompagnement et leurs précieux conseils.",
      "Je souhaite vivement que ces activités se poursuivent et touchent davantage d'élèves, car elles contribuent à notre épanouissement et à la construction d'une génération de jeunes responsables, bien informés et en bonne santé.",
    ],
    nom: "Ayiman N.",
    role: "Président du Club Santé SOS Dr TV, Lycée Tandjouaré",
  },
  {
    id: "francois-leger-koffi-k",
    t: "Je remercie avec fierté et joie notre professeur, Monsieur KODOM, et toute son équipe pour la réalisation de ce site merveilleux.",
    suite: [
      "Grâce à lui, nous avons enrichi notre mémoire et appris beaucoup de choses nouvelles. C'est pourquoi j'invite les camarades à rejoindre le club santé de Génie Imhotep. Je vous remercie.",
    ],
    nom: "François Léger Koffi K.",
    role: "Élève de Première D",
  },
  {
    id: "koffi-semanou-d",
    t: "Aujourd'hui, les jeunes sont plus accrochés à leurs mobiles qu'aux livres et aux documents. Le seul moyen de les faire étudier, c'est d'amener l'apprentissage vers le mobile.",
    suite: [
      "Donc je dirai un sincère merci à notre très cher professeur, le Dr KODOM, et toute son équipe pour la réalisation de ce site.",
      "Pour moi, le jeu Génie Imhotep du Club Santé SOS Dr TV m'a permis de jouer et de gagner des points tout en m'amusant. En répondant à des questions sur la santé sexuelle et reproductive, j'ai appris tant de choses.",
      "Je conseille à tous mes amis de jouer à ce jeu, car ça nous rend plus intelligents sur notre santé.",
    ],
    nom: "Koffi Semanou D.",
    role: "Élève de Première D, Lycée de Tokoin 1",
  },
  {
    id: "jeremie-a",
    t: "Ce site nous offre l'opportunité de participer à des jeux interactifs, de cumuler des points, de relever des défis intellectuels et d'obtenir des certifications attestant de nos performances.",
    suite: [
      "Je tiens à exprimer ma profonde gratitude au Prof. Dr Serge Michel KODOM pour cette remarquable initiative visant à mettre à la disposition des élèves et des étudiants une plateforme éducative aussi innovante qu'enrichissante.",
      "À titre personnel, cette plateforme constitue une véritable source d'épanouissement intellectuel. Elle m'a permis de stimuler davantage mes facultés mémorielles, d'accroître ma célérité dans la réflexion et de développer de nouvelles connaissances relatives aux enjeux de la santé. Elle représente également un précieux complément à mon parcours scolaire, notamment en Sciences de la Vie et de la Terre (SVT), en m'aidant à consolider certaines notions abordées en classe grâce à une approche pédagogique interactive, ludique et particulièrement captivante.",
      "Je voudrais, par conséquent, exhorter l'ensemble des élèves et étudiants, sans distinction de série, de filière ou de niveau d'études, à s'engager activement dans cette noble initiative qu'est le Club Santé SOS Docteur TV. C'est une opportunité exceptionnelle d'acquérir des connaissances, de cultiver la responsabilité individuelle et collective, et de devenir des ambassadeurs de la santé au sein de nos communautés.",
      "Club Santé SOS Docteur TV : « Ensemble pour une génération de jeunes en bonne santé, responsable et épanouie ! »",
      "Mes sincères remerciements au Prof. Dr Serge Michel KODOM ainsi qu'à toute son équipe pour leur dévouement, leur engagement et leur contribution à l'édification d'une jeunesse instruite, consciente et responsable.",
    ],
    nom: "Jérémie A.",
    role: "Élève de Première D, Lycée de Tokoin 1",
  },
];
