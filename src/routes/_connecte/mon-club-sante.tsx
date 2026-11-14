import { createFileRoute, Link, redirect, useRouter } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";

import { EspaceClubSante } from "@/components/clubs/MonClubSante";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { chargerAffiliationsDuClub, chargerMonClubSante, ErreurApi } from "@/lib/api/client";

// « Mon Club Santé » (spec 033) : l'espace partagé des encadreurs du club de leur établissement.
export const Route = createFileRoute("/_connecte/mon-club-sante")({
  gcTime: 0,
  beforeLoad: ({ context }) => {
    if (context.moi.role !== "encadreur") throw redirect({ to: "/mon-espace" });
  },
  loader: async () => {
    try {
      const [club, affiliations] = await Promise.all([
        chargerMonClubSante(),
        chargerAffiliationsDuClub(),
      ]);
      return { club, affiliations, message: null };
    } catch (e) {
      // Compte pas encore vérifié, ou pas encore rattaché : la page le dit simplement.
      if (e instanceof ErreurApi && (e.statut === 403 || e.statut === 404))
        return { club: null, affiliations: null, message: e.message };
      throw e;
    }
  },
  head: () => ({
    meta: [
      { title: "Mon Club Santé — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: PageMonClubSante,
});

function PageMonClubSante() {
  const { club, affiliations, message } = Route.useLoaderData();
  const router = useRouter();

  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-5xl">
        <Link
          to="/mon-espace"
          className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> Mon espace
        </Link>
        <p className="mt-6 flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
          <span className="h-1 w-8 rounded-full bg-primary" />
          Espace des encadreurs
        </p>
        <h1 className="mt-3 text-4xl leading-tight md:text-5xl">
          <span className="text-logo-blue">Mon Club</span>{" "}
          <span className="text-primary">Santé</span>
        </h1>
        {club && affiliations ? (
          <EspaceClubSante
            club={club}
            affiliations={affiliations}
            onRafraichir={() => router.invalidate()}
          />
        ) : (
          <p className="mt-6 rounded-3xl bg-white p-6 font-medium text-ink/80 shadow-card ring-1 ring-border">
            {message}
          </p>
        )}
      </div>
    </main>
  );
}
