import { useState } from "react";
import { ChevronLeft, ChevronRight, Quote } from "lucide-react";
import mascotte from "@/assets/mascotte-leadership.webp";

type Temoignage = {
  // La phrase affichée en grand ; la suite se déplie avec « Lire la suite ».
  t: string;
  suite?: string[];
  // Un élève n'apparaît que par son prénom et l'initiale de son nom (docs/RULES.md).
  nom: string;
  role: string;
};

// Témoignages publiés avec l'accord de leurs auteurs.
const temoignages: Temoignage[] = [
  {
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
    t: "Je remercie avec fierté et joie notre professeur, Monsieur KODOM, et toute son équipe pour la réalisation de ce site merveilleux.",
    suite: [
      "Grâce à lui, nous avons enrichi notre mémoire et appris beaucoup de choses nouvelles. C'est pourquoi j'invite les camarades à rejoindre le club santé de Génie Imhotep. Je vous remercie.",
    ],
    nom: "François Léger Koffi K.",
    role: "Élève de Première D",
  },
  {
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

export function TemoignagesSection() {
  const [actif, setActif] = useState(0);
  const [deplie, setDeplie] = useState(false);
  const x = temoignages[actif];
  const aller = (pas: number) => {
    setDeplie(false);
    setActif((a) => (a + pas + temoignages.length) % temoignages.length);
  };

  return (
    <section id="temoignages" className="scroll-mt-16 overflow-hidden bg-mist-soft py-20">
      <div className="mx-auto grid max-w-7xl items-center gap-10 px-5 lg:grid-cols-[2fr_3fr] lg:gap-14">
        <div data-reveal="left">
          <p className="text-sm font-extrabold uppercase text-primary">Témoignages</p>
          <h2 className="mt-2 text-4xl md:text-5xl">
            <span className="text-logo-blue">Les Clubs Santé</span>{" "}
            <span className="text-primary">en paroles</span>
          </h2>
          <p className="mt-4 text-muted-foreground">
            Découvre ce que les Clubs Santé ont changé pour celles et ceux qui les font vivre au
            quotidien.
          </p>
        </div>

        <figure
          data-reveal="right"
          className="relative isolate flex min-h-96 flex-col overflow-hidden rounded-[2rem] bg-card p-8 shadow-card md:p-12"
        >
          <Quote
            aria-hidden
            className="absolute right-6 top-6 -z-10 h-32 w-32 fill-current text-mist"
          />
          <div
            aria-hidden
            className="absolute -bottom-16 -right-10 -z-10 hidden h-64 w-64 rounded-full bg-sun sm:block"
          />
          <img
            src={mascotte}
            alt=""
            loading="lazy"
            width={1414}
            height={2000}
            className="absolute -bottom-20 right-0 -z-10 hidden w-48 motion-safe:animate-float sm:block"
          />
          <div
            key={actif}
            aria-live="polite"
            className="flex flex-1 flex-col animate-in fade-in slide-in-from-bottom-3 duration-500 sm:pr-44"
          >
            <blockquote className="flex-1 font-display text-3xl leading-tight text-logo-blue md:text-4xl">
              {x?.t}
            </blockquote>
            {x?.suite && (
              <div className="mt-5">
                <div
                  id={`temoignage-suite-${actif}`}
                  hidden={!deplie}
                  className="space-y-3 text-base text-foreground/80"
                >
                  {x.suite.map((paragraphe) => (
                    <p key={paragraphe}>{paragraphe}</p>
                  ))}
                </div>
                <button
                  type="button"
                  aria-expanded={deplie}
                  aria-controls={`temoignage-suite-${actif}`}
                  onClick={() => setDeplie((d) => !d)}
                  className="mt-3 text-sm font-extrabold text-primary underline-offset-4 hover:underline"
                >
                  {deplie ? "Réduire" : "Lire la suite"}
                </button>
              </div>
            )}
            <figcaption className="mt-6">
              <span className="block text-lg font-extrabold">{x?.nom}</span>
              <span className="block text-sm font-medium text-muted-foreground">{x?.role}</span>
            </figcaption>
          </div>
          {temoignages.length > 1 && (
            <div className="mt-6 flex items-center gap-2">
              <button
                type="button"
                aria-label="Témoignage précédent"
                onClick={() => aller(-1)}
                className="btn-fx flex h-11 w-11 items-center justify-center rounded-full border bg-card text-logo-blue"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <button
                type="button"
                aria-label="Témoignage suivant"
                onClick={() => aller(1)}
                className="btn-fx flex h-11 w-11 items-center justify-center rounded-full bg-primary text-primary-foreground"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
              {/* Un point par témoignage : situe celui qui est affiché et permet d'y aller directement. */}
              <div className="ml-3 flex gap-1.5">
                {temoignages.map((t, i) => (
                  <button
                    key={t.nom}
                    type="button"
                    aria-label={`Témoignage ${i + 1} sur ${temoignages.length}`}
                    aria-current={i === actif}
                    onClick={() => aller(i - actif)}
                    className={`h-2.5 rounded-full transition-all ${
                      i === actif ? "w-7 bg-primary" : "w-2.5 bg-logo-blue/25 hover:bg-logo-blue/50"
                    }`}
                  />
                ))}
              </div>
            </div>
          )}
        </figure>
      </div>
    </section>
  );
}
