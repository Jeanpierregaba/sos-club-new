import { Link } from "@tanstack/react-router";
import { ArrowRight, CalendarDays, MapPin } from "lucide-react";
import { retard } from "@/components/SiteMotion";
import fond from "@/assets/slide-genie.jpg";
import type { EvenementPublic } from "@/lib/api/client";
import { TYPES_EVENEMENT, dateEvenement } from "@/lib/agenda";

// Colonne de droite de la section Actualités : une photo sur toute la hauteur, teintée en bleu,
// et les rendez-vous posés dessus sur des cartes de verre. La teinte reste assez dense pour le texte blanc.
export function AgendaSidebar({ evenements }: { evenements: EvenementPublic[] }) {
  return (
    <aside
      id="agenda"
      data-reveal="right"
      className="relative isolate flex scroll-mt-24 flex-col overflow-hidden rounded-[2rem] p-4 text-white shadow-card md:p-5"
    >
      <img
        src={fond}
        alt=""
        loading="lazy"
        width={2000}
        height={1600}
        className="absolute inset-0 -z-20 size-full object-cover object-[50%_30%]"
      />
      <div
        aria-hidden
        className="absolute inset-0 -z-10 bg-linear-to-b from-logo-blue/95 via-logo-blue/85 to-sky/60"
      />

      <div className="flex items-center gap-4 p-2 pb-5">
        <span className="inline-flex size-12 shrink-0 items-center justify-center rounded-2xl bg-sun text-ink shadow-card">
          <CalendarDays className="size-6" />
        </span>
        <div>
          <h3 className="text-2xl leading-tight md:text-3xl">
            L’Agenda <span className="text-sun">des clubs</span>
          </h3>
          <p className="text-sm font-medium text-white/80">Note les prochains rendez-vous !</p>
        </div>
      </div>

      {evenements.length === 0 ? (
        <p className="rounded-2xl border border-white/25 bg-white/15 p-4 text-sm font-semibold backdrop-blur-xl">
          Aucun événement à venir pour le moment.
        </p>
      ) : (
        <ol className="space-y-3">
          {evenements.map((e, i) => (
            <li key={e.id} data-reveal style={retard(i + 1)}>
              <Link
                to="/agenda/$id"
                params={{ id: e.id }}
                className="group flex items-center gap-4 rounded-2xl border border-white/25 bg-white/15 p-3 shadow-[0_8px_24px_-12px] shadow-night/40 backdrop-blur-xl transition duration-300 hover:bg-white/25"
              >
                <span className="flex w-14 shrink-0 flex-col items-center rounded-xl bg-white py-2 text-logo-blue shadow-sm">
                  <span className="font-display text-2xl leading-none">
                    {dateEvenement(e.debut, { day: "numeric" })}
                  </span>
                  <span className="mt-0.5 text-[11px] font-bold uppercase text-logo-red">
                    {dateEvenement(e.debut, { month: "short" })}
                  </span>
                </span>
                <span className="min-w-0 flex-1">
                  <span className="text-[11px] font-extrabold uppercase tracking-wider text-sun">
                    {TYPES_EVENEMENT[e.type] ?? e.type}
                  </span>
                  <span className="mt-0.5 block font-bold leading-snug">{e.titre}</span>
                  <span className="mt-1 flex items-center gap-1 text-xs font-medium text-white/80">
                    <MapPin className="size-3.5 shrink-0" /> {e.en_ligne ? "En ligne" : e.lieu}
                  </span>
                </span>
                <ArrowRight className="size-4 shrink-0 text-white/60 transition duration-300 group-hover:translate-x-1 group-hover:text-white" />
              </Link>
            </li>
          ))}
        </ol>
      )}

      {/* L'espace restant laisse voir la photo, pour que la colonne descende aussi bas que les articles. */}
      <div className="mt-auto pt-8">
        <a
          href="/agenda"
          className="btn-fx flex w-full items-center justify-center gap-2 rounded-full bg-primary px-6 py-3 text-[15px] font-bold text-primary-foreground shadow-card"
        >
          Voir tout l’agenda <ArrowRight className="size-4" />
        </a>
      </div>
    </aside>
  );
}
