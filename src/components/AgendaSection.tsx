import { ArrowRight, MapPin } from "lucide-react";
import { retard } from "@/components/SiteMotion";
import fond from "@/assets/agenda-grandes-finales.jpg";
import story1 from "@/assets/story1.jpg";
import story2 from "@/assets/story2.jpg";
import slideGenie from "@/assets/slide-genie.jpg";

// La page /agenda n'existe pas encore.
const evenements = [
  {
    jour: 12,
    mois: "Oct",
    tag: "Concours",
    tc: "bg-logo-red",
    t: "Concours de production vidéo – Zéro grossesse et IST",
    lieu: "En ligne",
    img: story2,
    w: 992,
    h: 672,
    pos: "object-center",
  },
  {
    jour: 18,
    mois: "Oct",
    tag: "Formation",
    tc: "bg-grape",
    t: "Formation premiers secours pour les clubs",
    lieu: "Lycée de Kara",
    img: story1,
    w: 992,
    h: 672,
    pos: "object-center",
  },
  {
    jour: 25,
    mois: "Oct",
    tag: "Émission TV",
    tc: "bg-primary",
    t: "Enregistrement SOS Docteur TV – Spéciale Jeunes",
    lieu: "Studio Prof James",
    img: slideGenie,
    w: 2000,
    h: 1600,
    pos: "object-[50%_20%]",
  },
];

export function AgendaSection() {
  return (
    // clip-path limite la photo fixe à la section ; contrairement à background-attachment: fixed, cela fonctionne aussi sur iPhone.
    <section id="agenda" className="relative isolate scroll-mt-16 py-24 [clip-path:inset(0)]">
      <img
        src={fond}
        alt=""
        loading="lazy"
        width={2000}
        height={963}
        className="fixed inset-x-0 top-0 -z-20 h-lvh w-full object-cover"
      />
      <div aria-hidden className="absolute inset-0 -z-10 bg-night/30" />
      {/* Ce dégradé défile avec le texte : il reste derrière lui, même quand la photo fixe passe de zones sombres à des zones claires. */}
      <div
        aria-hidden
        className="absolute inset-x-0 top-0 -z-10 h-[30rem] bg-linear-to-b from-night/90 from-40% to-transparent"
      />

      <div className="mx-auto max-w-7xl px-5">
        <div data-reveal className="mx-auto max-w-3xl text-center text-primary-foreground">
          <h2 className="text-4xl md:text-5xl">
            L’Agenda <span className="text-primary">des clubs santé</span>
          </h2>
          <p className="mt-4">
            Concours, formations, émissions : repère les prochains rendez-vous des clubs santé et
            note-les pour ne rien manquer !
          </p>
        </div>

        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {evenements.map((e, i) => (
            <a
              key={e.t}
              href="/agenda"
              data-reveal
              style={retard(i)}
              className="card-fx group flex flex-col rounded-3xl bg-card p-3 shadow-card"
            >
              <div className="relative aspect-[4/3] overflow-hidden rounded-2xl">
                <img
                  src={e.img}
                  alt=""
                  loading="lazy"
                  width={e.w}
                  height={e.h}
                  className={`h-full w-full object-cover transition duration-700 group-hover:scale-110 ${e.pos}`}
                />
                <span className="absolute left-2 top-2 flex w-14 flex-col items-center rounded-2xl bg-card py-1.5 text-logo-blue shadow-card">
                  <span className="font-display text-2xl leading-none">{e.jour}</span>
                  <span className="mt-0.5 text-[11px] font-bold uppercase">{e.mois}</span>
                </span>
                <span
                  className={`${e.tc} absolute right-2 top-2 rounded-full px-3 py-1 text-xs font-extrabold uppercase text-primary-foreground`}
                >
                  {e.tag}
                </span>
              </div>

              <div className="flex flex-1 flex-col p-3 pt-4">
                <h3 className="flex-1 text-xl leading-tight text-logo-blue">{e.t}</h3>
                <p className="mt-2 flex items-center gap-1.5 text-sm font-medium text-muted-foreground">
                  <MapPin className="h-4 w-4 shrink-0" /> {e.lieu}
                </p>
                <span className="mt-3 flex items-center justify-between gap-2 border-t pt-3 text-sm font-bold text-logo-blue">
                  Voir l’événement
                  <span className="rounded-full bg-primary p-2 text-primary-foreground transition duration-300 group-hover:scale-110">
                    <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
                  </span>
                </span>
              </div>
            </a>
          ))}
        </div>

        <div className="mt-8 text-center">
          <a
            href="/agenda"
            className="btn-fx inline-block rounded-full bg-primary px-8 py-3 text-[15px] font-bold text-primary-foreground shadow-card"
          >
            Voir plus
          </a>
        </div>
      </div>
    </section>
  );
}
