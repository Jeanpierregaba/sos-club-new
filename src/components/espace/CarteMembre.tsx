import { Crown, Star } from "lucide-react";

import type { ProgressionJeux } from "@/lib/api/client";
import { NIVEAUX_JEUX } from "@/lib/bareme";

// La carte de membre numérique de l'élève (spec 034) : son pseudonyme, son club, ses quiz réussis et ses étoiles.
// Avec les 4 étoiles, elle passe au statut Gold, qui ouvre l'éligibilité au tirage au sort de fournitures scolaires.
export function CarteMembre({
  pseudonyme,
  club,
  jeux,
}: {
  pseudonyme: string;
  club: string | null;
  jeux: ProgressionJeux;
}) {
  const etoiles = new Set(jeux.niveaux.filter((n) => n.etoile).map((n) => n.niveau));
  return (
    <section
      aria-label="Ma carte de membre"
      data-gold={jeux.gold}
      className={`mt-6 overflow-hidden rounded-3xl p-6 shadow-card ring-1 sm:p-8 ${
        jeux.gold
          ? "bg-linear-to-br from-sun via-sun/80 to-tangerine/60 text-ink ring-sun"
          : "bg-white text-ink ring-border"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-extrabold uppercase tracking-widest text-logo-red">
            Carte de membre
          </p>
          <p className="mt-1 font-display text-3xl text-logo-blue">{pseudonyme}</p>
          <p className="text-sm font-semibold text-ink/70">{club ?? "Non affilié"}</p>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-sm font-extrabold ${
            jeux.gold ? "bg-ink text-sun" : "bg-mist-soft text-ink/70"
          }`}
        >
          {jeux.gold && <Crown aria-hidden className="size-4" />}
          {jeux.gold ? "GOLD" : "Membre"}
        </span>
      </div>
      <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
        <p className="font-semibold">
          <strong className="font-display text-2xl">{jeux.quiz_reussis}</strong> / 100 quiz Jeux
          réussis
        </p>
        <ul className="flex gap-2" aria-label="Étoiles">
          {NIVEAUX_JEUX.map((n, i) => (
            <li key={n.code} title={`Étoile ${i + 1} · ${n.nom}`}>
              <Star
                role="img"
                aria-label={`Étoile ${i + 1} ${etoiles.has(n.code) ? "obtenue" : "à obtenir"}`}
                className={`size-7 ${etoiles.has(n.code) ? "fill-logo-blue text-logo-blue" : "text-ink/25"}`}
              />
            </li>
          ))}
        </ul>
      </div>
      <dl className="mt-5 grid grid-cols-3 gap-3 text-center">
        {[
          { t: "Points des quiz", v: jeux.points_quiz },
          { t: "Points des étoiles", v: jeux.points_etoiles },
          { t: "Total Jeux", v: jeux.total },
        ].map((x) => (
          <div key={x.t} className="rounded-2xl bg-white/60 p-3 ring-1 ring-border">
            <dt className="text-xs font-bold text-ink/70">{x.t}</dt>
            <dd className="font-display text-xl tabular-nums">{x.v.toLocaleString("fr-FR")}</dd>
          </div>
        ))}
      </dl>
      {jeux.gold && (
        <p className="mt-4 text-sm font-semibold">
          Bravo : tes 4 étoiles te rendent éligible au tirage au sort de fournitures scolaires.
        </p>
      )}
    </section>
  );
}
