import { createFileRoute, Link } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";

import { RefusOuPanne } from "@/components/admin/RefusOuPanne";
import { adminListerClotures, type ClotureResume } from "@/lib/api/client";
import { ETATS_CLOTURE } from "@/lib/clotures";
import { dateCourte } from "@/lib/dates";

export const Route = createFileRoute("/_connecte/admin/points/clotures/")({
  loader: () => adminListerClotures(),
  gcTime: 0,
  errorComponent: RefusOuPanne,
  component: Clotures,
});

function action(semestre: ClotureResume): string {
  if (semestre.etat === "ouvert") return semestre.termine ? "Geler" : "En cours";
  if (semestre.etat === "gele") return "Contrôler";
  if (semestre.etat === "valide") return "Publier";
  return "Voir";
}

// Les clôtures de semestre (spec 037) : chaque semestre terminé se gèle, se contrôle, se valide puis se publie.
function Clotures() {
  const semestres = Route.useLoaderData();
  return (
    <section className="space-y-4">
      <p className="max-w-3xl text-sm font-medium text-muted-foreground">
        À la fin d'un semestre, gèle son classement national des élèves, contrôle les candidats,
        valide le Top 3 puis publie le palmarès. Une fois publié, il ne change plus.
      </p>
      {semestres.length === 0 ? (
        <p className="rounded-3xl border border-dashed p-8 text-center font-semibold text-muted-foreground">
          Aucun semestre n'a encore commencé.
        </p>
      ) : (
        <ul className="divide-y overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-border">
          {semestres.map((semestre) => {
            const etat = ETATS_CLOTURE[semestre.etat];
            const accessible = semestre.etat !== "ouvert" || semestre.termine;
            const contenu = (
              <>
                <div className="min-w-0 flex-1">
                  <p className="break-words font-bold text-ink">{semestre.libelle}</p>
                  <p className="text-xs font-semibold text-muted-foreground">
                    du {dateCourte(semestre.debut)} au {dateCourte(semestre.fin)}
                    {semestre.publie_le && ` · publié le ${dateCourte(semestre.publie_le)}`}
                  </p>
                </div>
                <span className={`rounded-full px-3 py-1 text-sm font-extrabold ${etat.classe}`}>
                  {etat.libelle}
                </span>
                <span className="flex items-center gap-1 text-sm font-bold text-primary">
                  {action(semestre)}
                  {accessible && <ChevronRight aria-hidden className="size-4" />}
                </span>
              </>
            );
            return (
              <li key={semestre.semestre_id}>
                {accessible ? (
                  <Link
                    to="/admin/points/clotures/$semestreId"
                    params={{ semestreId: semestre.semestre_id }}
                    className="flex flex-wrap items-center gap-3 px-4 py-3 hover:bg-mist-soft sm:px-5"
                  >
                    {contenu}
                  </Link>
                ) : (
                  <div className="flex flex-wrap items-center gap-3 px-4 py-3 sm:px-5">
                    {contenu}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
