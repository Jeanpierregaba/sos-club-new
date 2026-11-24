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
import { ContenuEnFrancais } from "@/components/ContenuEnFrancais";
import {
  COULEURS_NIVEAU,
  NIVEAUX,
  participants,
  plageEvenement,
  typeEvenement,
} from "@/lib/agenda";
import { m } from "@/paraglide/messages.js";

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
      { title: m.agenda_page_titre({ titre: loaderData?.titre ?? m.agenda_evenement() }) },
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
        <h1 className="text-4xl text-logo-blue">{m.agenda_introuvable()}</h1>
        <p className="mt-4 font-medium text-muted-foreground">{m.agenda_introuvable_texte()}</p>
        <Link to="/agenda" className="mt-8 inline-flex font-bold text-logo-blue hover:underline">
          {m.agenda_voir()}
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
        <FilAriane rubrique={m.menu_agenda()} page={evenement.titre} />
        <Link
          to="/agenda"
          className="mt-6 inline-flex items-center gap-1.5 text-sm font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> {m.agenda_tout()}
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
              {typeEvenement(evenement.type)}
            </span>
            {evenement.annule && (
              <span className="rounded-full bg-logo-red px-3 py-1 text-xs font-extrabold uppercase text-white">
                {m.agenda_annule()}
              </span>
            )}
            {!evenement.annule && evenement.complet && (
              <span className="rounded-full bg-sun px-3 py-1 text-xs font-extrabold uppercase text-ink">
                {m.agenda_complet()}
              </span>
            )}
          </div>
          <h1 className="mt-4 text-4xl leading-tight text-logo-blue md:text-5xl">
            {evenement.titre}
          </h1>
          <ContenuEnFrancais className="mt-3" />

          {evenement.annule && (
            <p className="mt-5 rounded-2xl bg-logo-red/10 px-4 py-3 font-semibold">
              {m.agenda_annule_texte()}
            </p>
          )}

          <dl className="mt-6 grid gap-4 text-sm font-semibold sm:grid-cols-2">
            <div className="flex gap-3">
              <CalendarDays className="size-5 shrink-0 text-logo-red" />
              <div>
                <dt className="sr-only">{m.agenda_date()}</dt>
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
                <dt className="sr-only">{m.agenda_lieu()}</dt>
                <dd className="break-words">
                  {evenement.en_ligne && evenement.lien ? (
                    <a
                      href={evenement.lien}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-logo-blue underline"
                    >
                      {m.agenda_en_ligne()}
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
                  <dt className="sr-only">{m.agenda_organisateur()}</dt>
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
                  <dt className="sr-only">{m.agenda_public()}</dt>
                  <dd>{evenement.public_vise}</dd>
                </div>
              </div>
            )}
          </dl>

          {evenement.objectif && (
            <section className="mt-8">
              <h2 className="text-xl text-logo-blue">{m.agenda_objectif()}</h2>
              <p className="mt-2 whitespace-pre-line font-medium">{evenement.objectif}</p>
            </section>
          )}
          <section className="mt-6">
            <h2 className="text-xl text-logo-blue">{m.agenda_programme()}</h2>
            <p className="mt-2 whitespace-pre-line font-medium">{evenement.description}</p>
          </section>

          {evenement.niveau === "club" && (
            <p className="mt-8 text-sm font-bold text-muted-foreground">
              {participants(evenement.participants, evenement.places, true)}
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
