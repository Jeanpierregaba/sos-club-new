import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { ArrowLeft, Sparkles } from "lucide-react";

import { BadgesParcours } from "@/components/certification/BadgesParcours";
import { CarteCertificat } from "@/components/certification/CarteCertificat";
import { CartePlace } from "@/components/certification/CartePlace";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { chargerMaCertification, ErreurApi, type MaCertification } from "@/lib/api/client";
import { prochainBadge, quizRestants } from "@/lib/certification";

export const Route = createFileRoute("/_connecte/certification/parcours/")({
  gcTime: 0,
  beforeLoad: ({ context }) => {
    if (context.moi.role === "admin") throw redirect({ to: "/admin/certification" });
  },
  loader: async () => {
    try {
      return { parcours: await chargerMaCertification(), refus: null };
    } catch (e) {
      // Un encadreur pas encore vérifié, ou un compte suspendu : l'API refuse, la page l'explique.
      if (e instanceof ErreurApi && e.statut === 403)
        return { parcours: null as MaCertification | null, refus: e.message };
      throw e;
    }
  },
  head: () => ({
    meta: [
      { title: "Ma certification — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: MaCertificationPage,
});

function MaCertificationPage() {
  const { parcours, refus } = Route.useLoaderData();
  const prochain = parcours ? prochainBadge(parcours.badges, parcours.reussies) : null;

  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-4xl space-y-8">
        <Link
          to="/mon-espace"
          className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> Mon espace
        </Link>
        <header>
          <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
            <span className="h-1 w-8 rounded-full bg-primary" />
            Parcours officiel
          </p>
          <h1 className="mt-3 text-4xl leading-tight md:text-5xl">
            <span className="text-logo-blue">Ma certification</span>{" "}
            <span className="text-primary">Génie Imhotep</span>
          </h1>
          {parcours && (
            <p className="mt-3 max-w-2xl text-muted-foreground">
              12 quiz à réussir dans l'ordre, chacun avec {parcours.nb_questions} questions
              chronométrées et {parcours.seuil} bonnes réponses pour le valider. Lis le fascicule
              avant de jouer : chaque palier débloque un badge, et les 12 quiz ton certificat.
            </p>
          )}
        </header>

        {refus && <p className="rounded-3xl bg-card p-6 font-semibold shadow-card">{refus}</p>}

        {parcours && (
          <>
            <section
              aria-label="Ta progression"
              className="rounded-3xl bg-card p-5 shadow-card sm:p-8"
            >
              <div className="flex flex-wrap items-end justify-between gap-3">
                <p className="font-display text-5xl text-logo-blue">
                  {parcours.reussies}
                  <span className="text-2xl text-muted-foreground"> / 12 quiz réussis</span>
                </p>
                {prochain && (
                  <p className="inline-flex items-center gap-2 rounded-full bg-sun/30 px-4 py-2 text-sm font-bold text-ink">
                    <Sparkles aria-hidden className="size-4" />
                    {prochain.manquent > 0
                      ? `Encore ${quizRestants(prochain.manquent)} pour le badge ${prochain.badge.nom}`
                      : `Badge ${prochain.badge.nom} en cours de délivrance`}
                  </p>
                )}
              </div>
              <div
                role="progressbar"
                aria-label="Quiz du parcours réussis"
                aria-valuemin={0}
                aria-valuemax={12}
                aria-valuenow={parcours.reussies}
                className="mt-4 h-3 overflow-hidden rounded-full bg-mist"
              >
                <div
                  className="h-full rounded-full bg-primary transition-[width]"
                  style={{ width: `${(parcours.reussies / 12) * 100}%` }}
                />
              </div>
              <div className="mt-6">
                <BadgesParcours badges={parcours.badges} />
              </div>
            </section>

            {parcours.certificat && <CarteCertificat certificat={parcours.certificat} />}

            <section aria-labelledby="titre-quiz">
              <h2 id="titre-quiz" className="font-sans text-xl font-extrabold text-logo-blue">
                Les 12 quiz du parcours
              </h2>
              <ol className="mt-4 space-y-3">
                {parcours.places.map((p) => (
                  <CartePlace key={p.place} place={p} seuil={parcours.seuil} />
                ))}
              </ol>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
