import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";

import { ApercuCarte } from "@/components/cartes/ApercuCarte";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { chargerMaCarte, ErreurApi, type MaCarte } from "@/lib/api/client";
import { TYPES_CARTE } from "@/lib/cartes";

export const Route = createFileRoute("/_connecte/ma-carte")({
  // Rien en cache : la carte porte le nom et le code du QR.
  gcTime: 0,
  beforeLoad: ({ context }) => {
    if (context.moi.role !== "eleve" && context.moi.role !== "encadreur")
      throw redirect({ to: "/mon-espace" });
  },
  loader: async () => {
    try {
      return { carte: await chargerMaCarte() };
    } catch (e) {
      // Un encadreur pas encore vérifié n'a pas de carte.
      if (e instanceof ErreurApi && e.statut === 404) return { carte: null as MaCarte | null };
      throw e;
    }
  },
  head: () => ({
    meta: [
      { title: "Ma carte — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: PageMaCarte,
});

// « Ma carte membre » ou « Ma carte encadreur » (spec 040).
function PageMaCarte() {
  const { carte } = Route.useLoaderData();
  const { moi } = Route.useRouteContext();
  const titre = carte
    ? TYPES_CARTE[carte.type]
    : moi.role === "eleve"
      ? "Carte membre"
      : "Carte encadreur";
  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-4xl">
        <Link
          to="/mon-espace"
          className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> Mon espace
        </Link>
        <h1 className="mt-4 text-4xl leading-tight md:text-5xl">
          <span className="text-logo-blue">Ma</span>{" "}
          <span className="text-primary">{titre.replace("Carte ", "carte ")}</span>
        </h1>
        <div className="mt-8">
          {carte ? (
            <ApercuCarte carte={carte} />
          ) : (
            <p className="max-w-xl rounded-3xl bg-white p-6 font-semibold shadow-card ring-1 ring-border">
              Ta carte encadreur arrivera quand l'équipe nationale aura vérifié ton compte.
            </p>
          )}
        </div>
      </div>
    </main>
  );
}
