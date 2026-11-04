import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import hygiene from "@/assets/campagne-hygiene.jpg";
import ecologie from "@/assets/campagne-ecologie.jpg";
import secourisme from "@/assets/campagne-secourisme.jpg";
import sensibilisation from "@/assets/campagne-sensibilisation.jpg";

// pos : le cadrage de l'affiche, pour garder l'action visible quand elle est rognée.
const campagnes = [
  {
    tag: "Hygiène",
    slogan: "Zéro microbe à l’école !",
    t: "Lavage des mains & hygiène",
    d: "Adopte le geste barrière essentiel : lave-toi les mains à l’eau courante et au savon après chaque récréation.",
    img: hygiene,
    pos: "object-[50%_30%]",
    alt: "La mascotte rouge du Club Santé se lave les mains au savon avec une élève",
    fond: "from-sky to-logo-blue",
  },
  {
    tag: "Écologie",
    slogan: "Un Togo vert pour demain",
    t: "1 élève, 1 arbre",
    d: "Chaque membre s’engage à planter et parrainer un jeune plant d’arbre dans son établissement ou son quartier.",
    img: ecologie,
    pos: "object-[50%_45%]",
    alt: "La mascotte verte du Club Santé plante un arbre avec un élève",
    fond: "from-primary to-leaf",
  },
  {
    tag: "Secourisme",
    slogan: "Savoir réagir, c’est sauver !",
    t: "Secourisme & premiers gestes",
    d: "Inscris-toi aux ateliers d’AIMES-AFRIQUE pour apprendre la réanimation et la prise en charge des malaises.",
    img: secourisme,
    pos: "object-[50%_75%]",
    alt: "La mascotte orange du Club Santé pratique un massage cardiaque sur un mannequin",
    fond: "from-rose to-logo-red",
  },
  {
    tag: "Sensibilisation",
    slogan: "S’informer en toute confiance",
    t: "Santé sexuelle & reproductive",
    d: "Des causeries éducatives anonymes pour lever les tabous et répondre à toutes tes questions.",
    img: sensibilisation,
    pos: "object-top",
    alt: "Affiche « Zéro grossesse et IST dans mon établissement » : la mascotte rouge discute avec deux élèves",
    fond: "from-tangerine to-logo-red",
  },
];

const DUREE = 7000;

// Slider des campagnes : le texte sur un fond propre à chaque campagne, l'affiche à droite.
export function CampagnesSection() {
  const [actif, setActif] = useState(0);
  const n = campagnes.length;
  const aller = (pas: number) => setActif((a) => (a + pas + n) % n);

  // Défilement automatique, relancé à chaque changement ; coupé si l'utilisateur limite les animations.
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const t = setTimeout(() => setActif((a) => (a + 1) % n), DUREE);
    return () => clearTimeout(t);
  }, [actif, n]);

  return (
    <section id="campagnes" className="mx-auto max-w-7xl scroll-mt-16 px-5 pb-20 pt-8">
      <div data-reveal>
        <p className="text-sm font-extrabold uppercase text-primary">Campagnes</p>
        <h2 className="mt-2 text-4xl md:text-5xl">
          <span className="text-logo-blue">Nos campagnes</span>{" "}
          <span className="text-primary">de sensibilisation</span>
        </h2>
      </div>

      <div
        data-reveal="zoom"
        aria-roledescription="carrousel"
        aria-label="Campagnes du Club Santé"
        className="relative isolate mt-8 grid overflow-hidden rounded-3xl text-white shadow-card lg:min-h-[34rem] lg:grid-cols-[1.3fr_1fr]"
      >
        {campagnes.map((c, i) => (
          <div
            key={c.tag}
            aria-hidden
            className={`absolute inset-0 -z-10 bg-linear-to-br ${c.fond} transition-opacity duration-700 ${i === actif ? "opacity-100" : "opacity-0"}`}
          />
        ))}
        <div
          aria-hidden
          className="pointer-events-none absolute -left-24 -top-24 -z-10 size-80 rounded-full border-[3rem] border-white/5"
        />

        {/* L'affiche : au-dessus sur mobile, à droite sur grand écran. */}
        <div className="relative aspect-[4/5] overflow-hidden sm:aspect-video lg:order-last lg:aspect-auto">
          {campagnes.map((c, i) => (
            <img
              key={c.tag}
              src={c.img}
              alt={c.alt}
              aria-hidden={i !== actif}
              loading="lazy"
              width={546}
              height={908}
              className={`absolute inset-0 size-full object-cover ${c.pos} transition duration-700 ease-out ${i === actif ? "scale-100 opacity-100" : "scale-105 opacity-0"}`}
            />
          ))}
        </div>

        <div className="flex flex-col p-7 md:p-10 lg:p-12">
          <div className="flex items-center justify-between gap-4">
            <span className="rounded-full bg-white/15 px-4 py-1.5 text-sm font-extrabold uppercase tracking-wide ring-1 ring-white/30">
              {campagnes[actif]?.tag}
            </span>
            <div className="flex rounded-2xl bg-black/15 p-1">
              <button
                type="button"
                onClick={() => aller(-1)}
                aria-label="Campagne précédente"
                className="inline-flex size-11 items-center justify-center rounded-xl transition hover:bg-white/15 active:scale-90"
              >
                <ChevronLeft className="size-5" />
              </button>
              <button
                type="button"
                onClick={() => aller(1)}
                aria-label="Campagne suivante"
                className="inline-flex size-11 items-center justify-center rounded-xl transition hover:bg-white/15 active:scale-90"
              >
                <ChevronRight className="size-5" />
              </button>
            </div>
          </div>

          {/* Toutes les slides partagent la même cellule : la hauteur reste celle de la plus longue. */}
          <div className="my-10 grid flex-1 items-center lg:my-14">
            {campagnes.map((c, i) => (
              <div
                key={c.tag}
                aria-hidden={i !== actif}
                className={`col-start-1 row-start-1 transition-[opacity,visibility,translate] ease-out ${i === actif ? "translate-y-0 opacity-100 delay-200 duration-500" : "invisible translate-y-3 opacity-0 duration-200"}`}
              >
                <p className="text-sm font-extrabold uppercase tracking-widest text-sun">
                  {c.slogan}
                </p>
                <h3 className="mt-3 text-4xl leading-[1.05] md:text-5xl">{c.t}</h3>
                <p className="mt-5 max-w-lg text-lg font-medium leading-relaxed text-white/90">
                  {c.d}
                </p>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between gap-4 border-t border-white/20 pt-6">
            <div className="flex items-center gap-2">
              {campagnes.map((c, i) => (
                <button
                  key={c.tag}
                  type="button"
                  onClick={() => setActif(i)}
                  aria-label={`Voir la campagne ${c.tag}`}
                  aria-current={i === actif}
                  className={`relative h-2.5 overflow-hidden rounded-full transition-all duration-300 ${i === actif ? "w-12 bg-white/30" : "w-2.5 bg-white/40 hover:bg-white/70"}`}
                >
                  {/* La barre se remplit pendant le temps d'affichage de la campagne. */}
                  {i === actif && (
                    <span
                      key={actif}
                      className="absolute inset-y-0 left-0 w-full rounded-full bg-white transition-[width] duration-[7s] ease-linear starting:w-0"
                    />
                  )}
                </button>
              ))}
            </div>
            <p aria-live="polite" className="text-sm font-extrabold uppercase">
              Campagne {actif + 1} / {n}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
