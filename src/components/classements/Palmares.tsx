import { Award } from "lucide-react";

import type { PalmaresPublic } from "@/lib/api/client";
import { formaterPoints } from "@/lib/classements";
import { dateCourte } from "@/lib/dates";

const COULEURS = [
  "bg-sun/30 ring-sun",
  "bg-mist-soft ring-border",
  "bg-[color-mix(in_oklch,var(--tangerine)_18%,white)] ring-tangerine/40",
];

// La règle d'égalité publiée (spec 037) : elle s'affiche avec le palmarès, comme le demande le cahier des charges.
export const REGLE_EX_AEQUO =
  "À égalité de points, l'élève qui a atteint son total le premier passe devant ; à la même seconde, l'ordre alphabétique du nom de joueur décide.";

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
        Top 3 national des élèves
      </p>
      <h2 id="titre-palmares" className="text-3xl">
        <span className="text-logo-blue">Palmarès des</span>{" "}
        <span className="text-primary">semestres</span>
      </h2>
      <p className="max-w-3xl text-sm font-medium text-muted-foreground">
        À la fin de chaque semestre, l'équipe nationale fige le classement, le contrôle puis publie
        le Top 3. {REGLE_EX_AEQUO}
      </p>
      {palmares.semestres.length === 0 ? (
        <p className="rounded-2xl border border-dashed p-6 text-center font-semibold text-muted-foreground">
          Le premier palmarès sera publié à la fin du semestre.
        </p>
      ) : (
        <div className="space-y-6">
          {palmares.semestres.map((semestre) => (
            <article key={`${semestre.libelle}-${semestre.debut}`} className="space-y-3">
              <h3 className="font-display text-xl text-logo-blue">
                {semestre.libelle}
                <span className="ml-2 text-sm font-semibold text-muted-foreground">
                  du {dateCourte(semestre.debut)} au {dateCourte(semestre.fin)}
                </span>
              </h3>
              <ol
                aria-label={`Lauréats de ${semestre.libelle}`}
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
                      <span className="text-base text-ink/60">pts</span>
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
