import { useState } from "react";
import { ChevronLeft, ChevronRight, Quote, UserRound } from "lucide-react";
import mascotte from "@/assets/mascotte-leadership.webp";

// Emplacements à remplacer par de vrais témoignages, avec l'accord de leurs auteurs.
const temoignages = [
  {
    t: "Texte du témoignage à venir.",
    nom: "Prénom Nom",
    role: "Élève, Club Santé de l’établissement",
  },
  { t: "Texte du témoignage à venir.", nom: "Prénom Nom", role: "Encadreur pédagogique" },
  { t: "Texte du témoignage à venir.", nom: "Prénom Nom", role: "Pair éducateur" },
];

export function TemoignagesSection() {
  const [actif, setActif] = useState(0);
  const x = temoignages[actif];
  const aller = (pas: number) =>
    setActif((a) => (a + pas + temoignages.length) % temoignages.length);

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
          <div className="mt-6 grid gap-3">
            {temoignages.map((p, i) => (
              <button
                key={i}
                type="button"
                aria-pressed={i === actif}
                onClick={() => setActif(i)}
                className={`flex w-full items-center gap-3 rounded-2xl border p-3 text-left transition duration-300 active:scale-[0.98] ${i === actif ? "border-primary bg-card shadow-card" : "border-transparent hover:translate-x-1 hover:bg-card"}`}
              >
                <span
                  className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full transition duration-300 ${i === actif ? "bg-primary text-primary-foreground" : "bg-mist text-logo-blue"}`}
                >
                  <UserRound className="h-5 w-5" />
                </span>
                <span className="min-w-0">
                  <span className="block font-extrabold leading-tight">{p.nom}</span>
                  <span className="block text-xs font-medium text-muted-foreground">{p.role}</span>
                </span>
              </button>
            ))}
          </div>
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
            <figcaption className="mt-6">
              <span className="block text-lg font-extrabold">{x?.nom}</span>
              <span className="block text-sm font-medium text-muted-foreground">{x?.role}</span>
            </figcaption>
          </div>
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
        </figure>
      </div>
    </section>
  );
}
