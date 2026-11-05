import { useEffect, useState, type ReactNode } from "react";
import { ArrowRight, Crown, Hourglass, Trophy } from "lucide-react";
import { EnTete } from "@/components/EnTete";
import { retard } from "@/components/SiteMotion";
import { editions, libelleSaison, ordinal, type Edition } from "@/lib/genie-imhotep-editions";

// Les éditions du Génie Imhotep, saison après saison : une ligne de temps dorée relie une carte par
// édition. Toute la carte mène à la page de l'édition, dans le Hall of Fame ou dans le Palmarès.

const dateLongue = (iso: string) =>
  new Date(iso).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });

// Les jours restants, calculés dans le navigateur : le HTML du serveur ne dépend pas de son horloge.
function JoursRestants({ cible }: { cible: string }) {
  const [jours, setJours] = useState<number | null>(null);
  useEffect(() => {
    setJours(Math.max(0, Math.ceil((new Date(cible).getTime() - Date.now()) / 86_400_000)));
  }, [cible]);
  return (
    <span className="font-display text-5xl leading-none tabular-nums text-logo-blue">
      {jours === null ? "--" : jours}
      <span className="ml-2 align-middle font-sans text-sm font-extrabold uppercase tracking-widest text-muted-foreground">
        jours
      </span>
    </span>
  );
}

function CarteEdition({ e, href, action }: { e: Edition; href: string; action: string }) {
  const aVenir = e.statut === "a-venir";
  return (
    <a
      href={href}
      className="group relative flex h-full flex-col overflow-hidden rounded-[2rem] bg-white shadow-card ring-1 ring-border transition duration-300 hover:-translate-y-1.5 hover:shadow-2xl focus-visible:ring-4 focus-visible:ring-primary"
    >
      {/* L'en-tête de la saison : doré pour une édition jouée, bleu ciel pour une édition à venir. */}
      <div
        className={`relative isolate overflow-hidden px-7 pb-8 pt-7 ${
          aVenir
            ? "bg-linear-to-br from-sky to-logo-blue text-white"
            : "bg-linear-to-br from-sun to-tangerine text-ink"
        }`}
      >
        <span
          aria-hidden
          className="absolute -right-10 -top-10 -z-10 size-48 rounded-full border-[1.5rem] border-white/25 transition duration-700 group-hover:scale-110"
        />
        <p className="text-xs font-extrabold uppercase tracking-widest opacity-80">
          {ordinal(e.numero)} édition · {aVenir ? "à venir" : "terminée"}
        </p>
        <p className="mt-2 font-display text-5xl leading-none tabular-nums md:text-6xl">
          {libelleSaison(e.id)}
        </p>
      </div>

      <div className="relative flex flex-1 flex-col px-7 pb-7 pt-10">
        <span
          aria-hidden
          className={`absolute -top-8 right-7 z-10 inline-flex size-16 items-center justify-center rounded-2xl shadow-card ring-4 ring-white ${
            aVenir ? "bg-white text-logo-blue" : "bg-ink text-sun"
          }`}
        >
          {aVenir ? (
            <Hourglass className="size-7 motion-safe:animate-[spin_6s_ease-in-out_infinite]" />
          ) : (
            <Trophy className="size-7" />
          )}
        </span>
        {aVenir ? (
          <>
            <p className="text-xs font-extrabold uppercase tracking-widest text-logo-red">
              Coup d’envoi dans
            </p>
            <p className="mt-2">
              {e.debut ? <JoursRestants cible={e.debut} /> : "Date bientôt annoncée"}
            </p>
            {e.debut && (
              <p className="mt-2 text-sm font-bold text-muted-foreground">
                Le {dateLongue(e.debut)}
              </p>
            )}
          </>
        ) : (
          <>
            <p className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-widest text-logo-red">
              <Crown aria-hidden className="size-4 text-tangerine" /> Champion national
            </p>
            <p className="mt-2 font-display text-3xl leading-tight text-logo-blue">{e.champion}</p>
          </>
        )}
        <span className="mt-auto inline-flex items-center gap-2 pt-6 font-bold text-primary">
          {action}
          <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
        </span>
      </div>
    </a>
  );
}

export function SectionEditions({
  base,
  sur,
  children,
}: {
  base: "hall-of-fame" | "palmares";
  sur: string;
  children: ReactNode;
}) {
  return (
    <section id="editions" className="mx-auto max-w-7xl scroll-mt-20 px-5 py-20">
      <EnTete sur={sur} bleu="Les éditions" vert="du championnat">
        {children}
      </EnTete>
      <ol className="relative mt-12 grid gap-8 md:grid-cols-2 lg:grid-cols-3">
        {/* La ligne de temps qui relie les saisons, sur grand écran. */}
        <span
          aria-hidden
          className="absolute -top-5 left-8 right-8 hidden border-t-2 border-dashed border-tangerine/50 md:block"
        />
        {editions.map((e, i) => {
          const aVenir = e.statut === "a-venir";
          return (
            <li key={e.id} data-reveal style={retard(i)} className="relative">
              <span
                aria-hidden
                className={`absolute -top-7 left-8 hidden size-4 rounded-full ring-4 ring-white md:block ${aVenir ? "bg-sky motion-safe:animate-pulse" : "bg-tangerine"}`}
              />
              <CarteEdition
                e={e}
                href={`/genie-imhotep/${base}/${e.id}`}
                action={
                  aVenir
                    ? "Découvrir la prochaine édition"
                    : base === "palmares"
                      ? "Voir le palmarès"
                      : "Revivre l’édition"
                }
              />
            </li>
          );
        })}
      </ol>
    </section>
  );
}
