import { Link } from "@tanstack/react-router";
import { Hourglass, Trophy } from "lucide-react";
import { editions, ordinal, type Edition } from "@/lib/genie-imhotep-editions";

// La frise des éditions du Génie Imhotep : une saison par médaillon, reliés par un fil pointillé comme les
// étapes d'un parcours. L'édition choisie est dorée ; une édition à venir porte un sablier et un point qui bat.
// Chaque médaillon est un lien (?edition=…) : une édition se partage et se retrouve avec « Précédent ».
export function FriseEditions({
  actuelle,
  vers,
}: {
  actuelle: Edition;
  vers: "/genie-imhotep/hall-of-fame" | "/genie-imhotep/palmares";
}) {
  return (
    <nav aria-label="Éditions du championnat" className="relative">
      <p className="text-xs font-extrabold uppercase tracking-widest text-white/60">
        Choisis une saison
      </p>
      <ol className="relative mt-1 -mx-2 flex snap-x gap-3 overflow-x-auto px-2 pb-6 pt-3 [scrollbar-width:none] sm:gap-5">
        {/* Le fil qui relie les saisons. */}
        <span
          aria-hidden
          className="pointer-events-none absolute left-6 right-6 top-1/2 -z-0 border-t-2 border-dashed border-white/25"
        />
        {editions.map((e) => {
          const active = e.id === actuelle.id;
          const aVenir = e.statut === "a-venir";
          const Icone = aVenir ? Hourglass : Trophy;
          return (
            <li key={e.id} className="relative shrink-0 snap-start">
              <Link
                to={vers}
                search={{ edition: e.id }}
                resetScroll={false}
                aria-current={active ? "page" : undefined}
                className={`group flex items-center gap-3 rounded-2xl py-2.5 pl-2.5 pr-5 ring-1 transition duration-300 active:scale-95 ${
                  active
                    ? "bg-sun text-ink shadow-[0_10px_30px_-10px_rgb(255_210_80/0.7)] ring-sun"
                    : "bg-night/70 text-white ring-white/20 backdrop-blur-sm hover:-translate-y-0.5 hover:ring-sun/60"
                }`}
              >
                <span
                  className={`relative inline-flex size-11 shrink-0 items-center justify-center rounded-xl ${
                    active ? "bg-ink text-sun" : "bg-white/10 text-sun"
                  }`}
                >
                  <Icone
                    className={`size-5 ${aVenir ? "motion-safe:animate-[spin_6s_ease-in-out_infinite]" : ""}`}
                  />
                  {aVenir && (
                    <span className="absolute -right-1 -top-1 flex size-3">
                      <span className="absolute inline-flex size-full rounded-full bg-logo-red opacity-75 motion-safe:animate-ping" />
                      <span className="relative inline-flex size-3 rounded-full bg-logo-red" />
                    </span>
                  )}
                </span>
                <span className="text-left">
                  <span
                    className={`block text-[11px] font-extrabold uppercase tracking-wider ${active ? "text-ink/70" : "text-white/60"}`}
                  >
                    {ordinal(e.numero)} édition · {aVenir ? "à venir" : "palmarès"}
                  </span>
                  <span className="block font-display text-2xl leading-tight tabular-nums">
                    {e.id.replace("-", " – ")}
                  </span>
                </span>
              </Link>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
