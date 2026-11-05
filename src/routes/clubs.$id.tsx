import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft, CalendarDays, MapPin, Sparkles } from "lucide-react";

import { FilAriane } from "@/components/FilAriane";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteMotion } from "@/components/SiteMotion";
import { chargerAxes, chargerFicheClub, ErreurApi } from "@/lib/api/client";
import { libelleAxes, libellesDesAxes } from "@/lib/clubs";
import { dateCourte } from "@/lib/dates";

export const Route = createFileRoute("/clubs/$id")({
  loader: async ({ params }) => {
    const [club, axes] = await Promise.all([
      chargerFicheClub(params.id),
      chargerAxes().catch(() => []),
    ]);
    return { club, axes };
  },
  head: () => ({
    meta: [
      { title: "Un Club Santé — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content:
          "La fiche publique d'un Club Santé : son établissement, sa Direction Régionale de l'Éducation et ses axes d'intervention.",
      },
    ],
  }),
  errorComponent: (props) =>
    props.error instanceof ErreurApi && props.error.statut === 404 ? (
      <ClubIntrouvable />
    ) : (
      <ServiceIndisponible {...props} />
    ),
  component: FicheClubPage,
});

function ClubIntrouvable() {
  return (
    <div className="min-h-screen bg-carnet text-ink">
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-5 py-24 text-center">
        <p className="font-display text-7xl text-primary">404</p>
        <h1 className="mt-3 text-4xl text-logo-blue">Ce club est introuvable</h1>
        <p className="mt-3 font-medium text-muted-foreground">
          Il n'existe pas, ou son ouverture n'a pas encore été validée par l'équipe nationale.
        </p>
        <Link
          to="/carte-des-clubs"
          className="mt-8 inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 font-bold text-primary-foreground"
        >
          <ArrowLeft className="size-4" /> Revenir à la carte des clubs
        </Link>
      </main>
      <SiteFooter />
    </div>
  );
}

function FicheClubPage() {
  const { club, axes } = Route.useLoaderData();
  const libelles = libellesDesAxes(axes);

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      <section className="relative isolate overflow-hidden bg-linear-to-br from-logo-blue to-night text-white">
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-[radial-gradient(oklch(1_0_0/0.14)_1.5px,transparent_1.5px)] bg-size-[22px_22px] [mask-image:linear-gradient(to_right,black,transparent_55%)]" />
          <div className="absolute -right-32 top-1/2 size-[32rem] -translate-y-1/2 rounded-full border-[2.5rem] border-white/5" />
        </div>
        <div className="mx-auto max-w-5xl px-5 pb-16 pt-8 md:pb-20 md:pt-12">
          <FilAriane rubrique="Vie du club" page="Fiche du club" clair />
          <div data-reveal="left" className="pt-10 md:pt-14">
            <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-sm font-bold backdrop-blur-sm">
              <Sparkles className="size-4 text-sun" /> Club Santé actif
            </p>
            <h1 className="mt-5 max-w-3xl text-4xl leading-tight md:text-6xl">{club.nom}</h1>
            <p className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 text-lg font-semibold text-white/85">
              <MapPin aria-hidden className="size-5 text-sun" />
              {club.etablissement.nom}
              <span className="text-white/60">
                · {club.etablissement.iesg} · DRE {club.etablissement.dre}
              </span>
            </p>
            {club.actif_le && (
              <p className="mt-2 flex items-center gap-2 text-sm font-semibold text-white/70">
                <CalendarDays aria-hidden className="size-4" /> Club actif depuis le{" "}
                {dateCourte(club.actif_le)}
              </p>
            )}
          </div>
        </div>
      </section>

      <main className="mx-auto max-w-5xl px-5 pb-20 pt-10">
        <section className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-border md:p-10">
          <h2 className="text-2xl">
            <span className="text-logo-blue">Le</span> <span className="text-primary">club</span>
          </h2>
          <p className="mt-3 max-w-3xl whitespace-pre-line font-medium leading-relaxed text-ink/80">
            {club.description ??
              "Les membres de ce club détailleront bientôt ses actions ici. En attendant, contacte l'établissement pour en savoir plus."}
          </p>

          <h3 className="mt-8 text-lg font-extrabold text-ink">Axes d'intervention</h3>
          {club.axes.length === 0 ? (
            <p className="mt-2 font-medium text-muted-foreground">
              Les axes seront précisés par le club.
            </p>
          ) : (
            <ul className="mt-3 flex flex-wrap gap-2">
              {club.axes.map((code) => (
                <li
                  key={code}
                  className="rounded-full bg-mist-soft px-4 py-2 text-sm font-bold text-ink ring-1 ring-border"
                >
                  {libelleAxes([code], libelles)}
                </li>
              ))}
            </ul>
          )}

          <div className="mt-8 rounded-2xl bg-mist-soft p-4 text-sm font-medium text-muted-foreground">
            Seuls le nom du club, son établissement et ses axes sont publics. Les membres et les
            activités du club arriveront avec les prochaines étapes.
          </div>

          <Link
            to="/carte-des-clubs"
            className="mt-8 inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
          >
            <ArrowLeft className="size-4" /> Tous les clubs sur la carte
          </Link>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
