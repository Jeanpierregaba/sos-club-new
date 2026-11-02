import { useState } from "react";
import story1 from "@/assets/story1.jpg";
import story2 from "@/assets/story2.jpg";
import slideAxes from "@/assets/slide-axes.jpg";
import slideClubs from "@/assets/slide-clubs.webp";
import slideGenie from "@/assets/slide-genie.jpg";
import slideMascottes from "@/assets/slide-mascottes.jpg";

const TOUS = "Tous";
const tags = [TOUS, "Génie Imhotep", "Vie des clubs", "Sports & Secourisme", "TV & Médias"];

const photos = [
  {
    tag: "Vie des clubs",
    img: slideClubs,
    w: 1493,
    h: 1053,
    pos: "object-center",
    alt: "Des élèves en t-shirt Club Santé, affiches en main, saluent un officiel",
  },
  {
    tag: "Génie Imhotep",
    img: slideGenie,
    w: 2000,
    h: 1600,
    pos: "object-[50%_20%]",
    alt: "Trois élèves en polo bleu au pupitre de la compétition Génie Imhotep",
  },
  {
    tag: "Sports & Secourisme",
    img: story1,
    w: 992,
    h: 672,
    pos: "object-center",
    alt: "Une élève s'entraîne au massage cardiaque sur un mannequin",
  },
  {
    tag: "Vie des clubs",
    img: slideAxes,
    w: 2000,
    h: 1228,
    pos: "object-center",
    alt: "Une salle d'élèves en t-shirt vert applaudit debout, sous le drapeau du Togo",
  },
  {
    tag: "TV & Médias",
    img: story2,
    w: 992,
    h: 672,
    pos: "object-center",
    alt: "Une élève en interviewe une autre devant une caméra",
  },
  {
    tag: "Génie Imhotep",
    img: slideMascottes,
    w: 1514,
    h: 1600,
    pos: "object-[50%_25%]",
    alt: "Remise du trophée de champion national Génie Imhotep à une élève en t-shirt orange",
  },
];

export function GalerieSection() {
  const [filtre, setFiltre] = useState(TOUS);
  const visibles = filtre === TOUS ? photos : photos.filter((p) => p.tag === filtre);

  return (
    <section id="galerie" className="scroll-mt-16 bg-mist-soft py-20">
      <div className="mx-auto max-w-7xl px-5">
        <div data-reveal className="grid items-center gap-6 lg:grid-cols-[1fr_auto] lg:gap-10">
          <div>
            <h2 className="text-4xl md:text-5xl">
              <span className="text-logo-blue">Les Clubs Santé</span>{" "}
              <span className="text-primary">en images</span>
            </h2>
            <p className="mt-4 max-w-xl text-muted-foreground">
              Revis en images les moments forts des Clubs Santé : compétitions, formations et
              actions de terrain.
            </p>
          </div>
          <div className="flex flex-wrap gap-2 lg:max-w-2xl lg:justify-end">
            {tags.map((t) => (
              <button
                key={t}
                type="button"
                aria-pressed={filtre === t}
                onClick={() => setFiltre(t)}
                className={`rounded-full border px-4 py-2 text-sm font-bold transition duration-200 active:scale-95 ${filtre === t ? "border-primary bg-primary text-primary-foreground" : "bg-card text-logo-blue hover:-translate-y-0.5 hover:border-primary"}`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-8 grid grid-cols-2 gap-3 md:grid-cols-3 md:gap-4">
          {visibles.map((p) => (
            <figure
              key={p.img}
              className="group relative overflow-hidden rounded-2xl shadow-card animate-in fade-in duration-300 md:rounded-3xl"
            >
              <img
                src={p.img}
                alt={p.alt}
                loading="lazy"
                width={p.w}
                height={p.h}
                className={`aspect-[4/3] w-full object-cover transition duration-500 group-hover:scale-105 ${p.pos}`}
              />
              <figcaption className="absolute bottom-2 left-2 rounded-full bg-black/60 px-2.5 py-1 text-[11px] font-bold text-primary-foreground backdrop-blur-sm md:bottom-3 md:left-3 md:text-xs">
                {p.tag}
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}
