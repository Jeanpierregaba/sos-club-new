import { useState } from "react";
import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { ArrowLeft, CalendarDays, Globe, MapPin, Target, Users } from "lucide-react";

import { ChoixReponse } from "@/components/agenda/ChoixReponse";
import { FilAriane } from "@/components/FilAriane";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { ErreurApi, chargerEvenement } from "@/lib/api/client";
import type { EvenementPublic } from "@/lib/api/client";
import { COULEURS_NIVEAU, NIVEAUX, TYPES_EVENEMENT, plageEvenement } from "@/lib/agenda";

export const Route = createFileRoute("/agenda_/$id")({
  loader: async ({ params }) => {
    try {
      return await chargerEvenement(params.id);
    } catch (e) {
      if (e instanceof ErreurApi && (e.statut === 404 || e.statut === 422)) throw notFound();
      throw e;
    }
  },
  head: ({ loaderData }) => ({
    meta: [
      { title: `${loaderData?.titre ?? "Événement"} — Agenda des Clubs Santé` },
      { name: "description", content: loaderData?.description.slice(0, 160) ?? "" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  notFoundComponent: Introuvable,
  component: PageEvenement,
});

function Introuvable() {
  return (
    <div className="min-h-screen bg-carnet text-ink">
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-5 py-20 text-center">
        <h1 className="text-4xl text-logo-blue">Cet événement n'existe pas</h1>
        <p className="mt-4 font-medium text-muted-foreground">
          Il a peut-être été retiré de l'agenda, ou il attend encore la validation de l'équipe.
        </p>
        <Link to="/agenda" className="mt-8 inline-flex font-bold text-logo-blue hover:underline">
          Voir l'agenda
        </Link>
      </main>
      <SiteFooter />
    </div>
  );
}

function PageEvenement() {
  const charge = Route.useLoaderData();
  const [evenement, setEvenement] = useState<EvenementPublic>(charge);
  const { couleur } = COULEURS_NIVEAU[evenement.niveau];

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteHeader />
      <main className="mx-auto max-w-4xl px-5 pb-20 pt-8">
        <FilAriane rubrique="Agenda" page={evenement.titre} />
        <Link
          to="/agenda"
          className="mt-6 inline-flex items-center gap-1.5 text-sm font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> Tout l'agenda
        </Link>

        <article className="mt-6 rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-border md:p-10">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className="rounded-full px-3 py-1 text-xs font-extrabold uppercase text-white"
              style={{ backgroundColor: couleur }}
            >
              {NIVEAUX[evenement.niveau].court}
            </span>
            <span className="rounded-full bg-mist px-3 py-1 text-xs font-extrabold uppercase text-logo-blue">
              {TYPES_EVENEMENT[evenement.type] ?? evenement.type}
            </span>
            {evenement.annule && (
              <span className="rounded-full bg-logo-red px-3 py-1 text-xs font-extrabold uppercase text-white">
                Annulé
              </span>
            )}
            {!evenement.annule && evenement.complet && (
              <span className="rounded-full bg-sun px-3 py-1 text-xs font-extrabold uppercase text-ink">
                Complet
              </span>
            )}
          </div>
          <h1 className="mt-4 text-4xl leading-tight text-logo-blue md:text-5xl">
            {evenement.titre}
          </h1>

          {evenement.annule && evenement.motif_annulation && (
            <p className="mt-5 rounded-2xl bg-logo-red/10 px-4 py-3 font-semibold">
              Annulé : {evenement.motif_annulation}
            </p>
          )}

          <dl className="mt-6 grid gap-4 text-sm font-semibold sm:grid-cols-2">
            <div className="flex gap-3">
              <CalendarDays className="size-5 shrink-0 text-logo-red" />
              <div>
                <dt className="sr-only">Date</dt>
                <dd>{plageEvenement(evenement.debut, evenement.fin)}</dd>
              </div>
            </div>
            <div className="flex min-w-0 gap-3">
              {evenement.en_ligne ? (
                <Globe className="size-5 shrink-0 text-logo-red" />
              ) : (
                <MapPin className="size-5 shrink-0 text-logo-red" />
              )}
              <div className="min-w-0">
                <dt className="sr-only">Lieu</dt>
                <dd className="break-words">
                  {evenement.en_ligne && evenement.lien ? (
                    <a
                      href={evenement.lien}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-logo-blue underline"
                    >
                      En ligne
                    </a>
                  ) : (
                    evenement.lieu
                  )}
                </dd>
              </div>
            </div>
            {evenement.club && (
              <div className="flex gap-3">
                <Users className="size-5 shrink-0 text-logo-red" />
                <div>
                  <dt className="sr-only">Organisateur</dt>
                  <dd>
                    {evenement.club}
                    {evenement.etablissement && (
                      <span className="block font-medium text-muted-foreground">
                        {evenement.etablissement}
                      </span>
                    )}
                  </dd>
                </div>
              </div>
            )}
            {evenement.public_vise && (
              <div className="flex gap-3">
                <Target className="size-5 shrink-0 text-logo-red" />
                <div>
                  <dt className="sr-only">Public visé</dt>
                  <dd>{evenement.public_vise}</dd>
                </div>
              </div>
            )}
          </dl>

          {evenement.objectif && (
            <section className="mt-8">
              <h2 className="text-xl text-logo-blue">Objectif</h2>
              <p className="mt-2 whitespace-pre-line font-medium">{evenement.objectif}</p>
            </section>
          )}
          <section className="mt-6">
            <h2 className="text-xl text-logo-blue">Programme</h2>
            <p className="mt-2 whitespace-pre-line font-medium">{evenement.description}</p>
          </section>

          {evenement.niveau === "club" && (
            <p className="mt-8 text-sm font-bold text-muted-foreground">
              {evenement.participants} participant{evenement.participants > 1 ? "s" : ""}
              {evenement.places ? ` sur ${evenement.places} places` : ""}
            </p>
          )}

          {evenement.peut_repondre && (
            <div className="mt-6">
              <ChoixReponse evenement={evenement} onReponse={setEvenement} />
            </div>
          )}
        </article>
      </main>
      <SiteFooter />
    </div>
  );
}
