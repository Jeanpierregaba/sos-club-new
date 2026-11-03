import { ArrowRight, CalendarDays, MapPin } from "lucide-react";
import { retard } from "@/components/SiteMotion";
import fond from "@/assets/slide-genie.jpg";

// La page /agenda n'existe pas encore.
const evenements = [
  {
    jour: 12,
    mois: "Oct",
    tag: "Concours",
    tc: "text-rose",
    t: "Concours de production vidéo – Zéro grossesse et IST",
    lieu: "En ligne",
  },
  {
    jour: 18,
    mois: "Oct",
    tag: "Formation",
    tc: "text-sky",
    t: "Formation premiers secours pour les clubs",
    lieu: "Lycée de Kara",
  },
  {
    jour: 25,
    mois: "Oct",
    tag: "Émission TV",
    tc: "text-primary",
    t: "Enregistrement SOS Docteur TV – Spéciale Jeunes",
    lieu: "Studio Prof James",
  },
];

// Colonne de droite de la section Actualités : les prochains rendez-vous en lignes, sur fond sombre.
export function AgendaSidebar() {
  return (
    <aside
      id="agenda"
      data-reveal="right"
      className="relative isolate flex scroll-mt-24 flex-col overflow-hidden rounded-[2rem] bg-night text-white shadow-card"
    >
      <span
        aria-hidden
        className="absolute -right-16 -top-16 -z-10 size-56 rounded-full bg-primary/25 blur-3xl"
      />
      <div className="flex items-center gap-4 p-6 pb-4 md:p-7 md:pb-5">
        <span className="inline-flex size-12 shrink-0 items-center justify-center rounded-2xl bg-primary">
          <CalendarDays className="size-6" />
        </span>
        <div>
          <h3 className="text-2xl leading-tight md:text-3xl">
            L’Agenda <span className="text-primary">des clubs</span>
          </h3>
          <p className="text-sm text-white/60">Note les prochains rendez-vous !</p>
        </div>
      </div>

      <ol className="mx-3 divide-y divide-white/10 border-t border-white/10">
        {evenements.map((e, i) => (
          <li key={e.t} data-reveal style={retard(i + 1)}>
            <a
              href="/agenda"
              className="group flex items-center gap-4 rounded-2xl px-3 py-4 transition-colors duration-300 hover:bg-white/5"
            >
              <span className="flex w-14 shrink-0 flex-col items-center rounded-2xl bg-white/10 py-2 ring-1 ring-white/10 transition-colors duration-300 group-hover:bg-primary">
                <span className="font-display text-2xl leading-none">{e.jour}</span>
                <span className="mt-0.5 text-[11px] font-bold uppercase text-white/70 group-hover:text-white">
                  {e.mois}
                </span>
              </span>
              <span className="min-w-0 flex-1">
                <span className={`text-[11px] font-extrabold uppercase tracking-wider ${e.tc}`}>
                  {e.tag}
                </span>
                <span className="mt-0.5 block font-bold leading-snug">{e.t}</span>
                <span className="mt-1 flex items-center gap-1 text-xs font-medium text-white/60">
                  <MapPin className="size-3.5 shrink-0" /> {e.lieu}
                </span>
              </span>
              <ArrowRight className="size-4 shrink-0 text-white/40 transition duration-300 group-hover:translate-x-1 group-hover:text-primary" />
            </a>
          </li>
        ))}
      </ol>

      {/* La photo occupe la place restante, pour que la colonne descende aussi bas que les articles. */}
      <div className="relative mt-4 flex min-h-56 flex-1 items-end p-6 md:p-7">
        <img
          src={fond}
          alt=""
          loading="lazy"
          width={2000}
          height={1600}
          className="absolute inset-0 -z-10 size-full object-cover object-[50%_30%] [mask-image:linear-gradient(to_bottom,transparent,black_45%)]"
        />
        <a
          href="/agenda"
          className="btn-fx flex w-full items-center justify-center gap-2 rounded-full bg-primary px-6 py-3 text-[15px] font-bold shadow-card"
        >
          Voir tout l’agenda <ArrowRight className="size-4" />
        </a>
      </div>
    </aside>
  );
}
