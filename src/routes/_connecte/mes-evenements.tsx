import { createFileRoute, Link, redirect } from "@tanstack/react-router";

import { ChoixReponse } from "@/components/agenda/ChoixReponse";
import { PageArticle } from "@/components/articles/PageArticle";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { chargerMesEvenements } from "@/lib/api/client";
import { plageEvenement } from "@/lib/agenda";

// Les événements à venir de mon club (spec 041) : je réponds jusqu'au début de chacun.
export const Route = createFileRoute("/_connecte/mes-evenements")({
  gcTime: 0,
  beforeLoad: ({ context }) => {
    if (context.moi.role !== "eleve") throw redirect({ to: "/mon-espace" });
  },
  loader: () => chargerMesEvenements(),
  head: () => ({
    meta: [
      { title: "Mes événements — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: MesEvenements,
});

function MesEvenements() {
  const evenements = Route.useLoaderData();
  return (
    <PageArticle titre="Mes" accent="événements" retour="club">
      {evenements.length === 0 ? (
        <p className="rounded-[1.75rem] border border-dashed p-8 text-center font-semibold text-muted-foreground">
          Ton club n'a pas d'événement à venir pour le moment.{" "}
          <Link to="/agenda" className="text-logo-blue underline">
            Voir tout l'agenda
          </Link>
        </p>
      ) : (
        <ul className="grid gap-5">
          {evenements.map((e) => (
            <li
              key={e.id}
              className="rounded-[1.75rem] bg-white p-5 shadow-card ring-1 ring-border md:p-7"
            >
              <Link
                to="/agenda/$id"
                params={{ id: e.id }}
                className="text-xl font-extrabold hover:underline"
              >
                {e.titre}
              </Link>
              <p className="mt-1 text-sm font-bold text-logo-blue">
                {plageEvenement(e.debut, e.fin)}
              </p>
              <p className="mt-1 text-sm font-semibold text-muted-foreground">
                {e.en_ligne ? "En ligne" : e.lieu}
                {e.annule && " · Annulé"}
              </p>
              {e.peut_repondre && (
                <div className="mt-4">
                  <ChoixReponse evenement={e} />
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </PageArticle>
  );
}
