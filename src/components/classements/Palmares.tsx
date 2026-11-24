import { Award } from "lucide-react";

import type { PalmaresPublic } from "@/lib/api/client";
import { formaterPoints, regleExAequo } from "@/lib/classements";
import { dateCourte } from "@/lib/dates";
import { m } from "@/paraglide/messages.js";

const COULEURS = [
  "bg-sun/30 ring-sun",
  "bg-mist-soft ring-border",
  "bg-[color-mix(in_oklch,var(--tangerine)_18%,white)] ring-tangerine/40",
];

// Le palmarès des semestres clôturés (spec 037) : Grand Champion, Vice-Champion et Jeune Talent, par leur nom de
// joueur, leur club et leur DRE. Rien d'autre n'est public.
export function Palmares({ palmares }: { palmares: PalmaresPublic }) {
  return (
    <section
      id="palmares"
      aria-labelledby="titre-palmares"
      className="scroll-mt-24 space-y-4 rounded-3xl bg-white p-5 shadow-sm ring-1 ring-border sm:p-8"
    >
      <p className="text-xs font-extrabold uppercase tracking-widest text-logo-red">
        {m.palmares_sur()}
      </p>
      <h2 id="titre-palmares" className="text-3xl">
        <span className="text-logo-blue">{m.palmares_bleu()}</span>{" "}
        <span className="text-primary">{m.palmares_vert()}</span>
      </h2>
      <p className="max-w-3xl text-sm font-medium text-muted-foreground">
        {m.palmares_texte()} {regleExAequo()}
      </p>
      {palmares.semestres.length === 0 ? (
        <p className="rounded-2xl border border-dashed p-6 text-center font-semibold text-muted-foreground">
          {m.palmares_premier()}
        </p>
      ) : (
        <div className="space-y-6">
          {palmares.semestres.map((semestre) => (
            <article key={`${semestre.libelle}-${semestre.debut}`} className="space-y-3">
              <h3 className="font-display text-xl text-logo-blue">
                {semestre.libelle}
                <span className="ml-2 text-sm font-semibold text-muted-foreground">
                  {m.palmares_du_au({
                    debut: dateCourte(semestre.debut),
                    fin: dateCourte(semestre.fin),
                  })}
                </span>
              </h3>
              <ol
                aria-label={m.palmares_laureats({ semestre: semestre.libelle })}
                className="grid gap-3 sm:grid-cols-3"
              >
                {semestre.laureats.map((laureat) => (
                  <li
                    key={laureat.place}
                    className={`rounded-3xl p-5 ring-1 ${COULEURS[laureat.place - 1]}`}
                  >
                    <p className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-wider text-logo-blue">
                      <Award aria-hidden className="size-5 text-primary" /> {laureat.distinction}
                    </p>
                    <p className="mt-2 break-words font-display text-2xl text-ink">
                      {laureat.pseudonyme}
                    </p>
                    <p className="mt-1 text-sm font-semibold text-muted-foreground">
                      {[laureat.club, laureat.dre].filter(Boolean).join(" · ")}
                    </p>
                    <p className="mt-3 font-display text-2xl text-primary">
                      {formaterPoints(laureat.points)}{" "}
                      <span className="text-base text-ink/60">{m.certif_pts()}</span>
                    </p>
                  </li>
                ))}
              </ol>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
