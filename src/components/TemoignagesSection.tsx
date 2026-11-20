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
            <div className="mt-6 flex gap-2">
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
            </div>
          )}
        </figure>
      </div>
    </section>
  );
}
