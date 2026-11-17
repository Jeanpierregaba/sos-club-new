import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { CalendarPlus } from "lucide-react";

import { PageArticle } from "@/components/articles/PageArticle";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { ErreurApi, chargerAgendaDuClub } from "@/lib/api/client";
import { ETATS_EVENEMENT, depuisLome, plageEvenement } from "@/lib/agenda";

// L'agenda du club (spec 041) : ses encadreurs vérifiés et son président proposent les événements, l'équipe les
// valide avant toute publication.
export const Route = createFileRoute("/_connecte/mon-club/agenda/")({
  gcTime: 0,
  loader: async () => {
    try {
      return await chargerAgendaDuClub();
    } catch (e) {
      if (e instanceof ErreurApi && e.statut === 403) throw redirect({ to: "/mon-espace" });
      throw e;
    }
  },
  head: () => ({
    meta: [
      { title: "Agenda du club — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: AgendaDuClub,
});

function AgendaDuClub() {
  const agenda = Route.useLoaderData();
  return (
    <PageArticle titre="Agenda" accent="du club" retour="club">
      <p className="-mt-2 mb-6 font-semibold text-muted-foreground">{agenda.club}</p>
      <Link
        to="/mon-club/agenda/nouveau"
        className="btn-fx inline-flex h-12 items-center gap-2 rounded-full bg-primary px-6 font-bold text-primary-foreground"
      >
        <CalendarPlus className="size-5" /> Proposer un événement
      </Link>
      <p className="mt-3 text-sm font-medium text-muted-foreground">
        Un événement n'apparaît dans l'agenda public qu'après la validation de l'équipe nationale.
      </p>

      {agenda.evenements.length === 0 ? (
        <p className="mt-8 rounded-[1.75rem] border border-dashed p-8 text-center font-semibold text-muted-foreground">
          Aucun événement pour l'instant.
        </p>
      ) : (
        <ul className="mt-8 grid gap-4">
          {agenda.evenements.map((e) => {
            const titre =
              typeof e.champs["titre"] === "string" ? e.champs["titre"] : "Événement sans titre";
            const debut = typeof e.champs["debut"] === "string" ? e.champs["debut"] : null;
            const fin = typeof e.champs["fin"] === "string" ? e.champs["fin"] : null;
            return (
              <li key={e.id}>
                <Link
                  to="/mon-club/agenda/$id"
                  params={{ id: e.id }}
                  className="block rounded-[1.5rem] bg-white p-5 shadow-card ring-1 ring-border transition hover:ring-logo-blue"
                >
                  <span className="flex flex-wrap items-center gap-2 text-xs font-extrabold uppercase">
                    <span className="rounded-full bg-mist px-2.5 py-0.5 text-logo-blue">
                      {e.annule_le ? "Annulé" : (ETATS_EVENEMENT[e.etat] ?? e.etat)}
                    </span>
                    {e.publie && !e.annule_le && (
                      <span className="text-primary">
                        {e.participants} participant{e.participants > 1 ? "s" : ""}
                      </span>
                    )}
                  </span>
                  <span className="mt-2 block text-lg font-extrabold">{titre}</span>
                  {debut && fin && (
                    <span className="mt-1 block text-sm font-semibold text-muted-foreground">
                      {plageEvenement(depuisLome(debut), depuisLome(fin))}
                    </span>
                  )}
                  <span className="mt-1 block text-xs font-semibold text-muted-foreground">
                    Proposé par {e.de_moi ? "toi" : e.auteur}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </PageArticle>
  );
}
