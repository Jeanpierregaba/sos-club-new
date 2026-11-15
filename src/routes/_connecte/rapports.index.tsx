import { createFileRoute, Link, redirect, useNavigate } from "@tanstack/react-router";
import { ArrowLeft, Plus } from "lucide-react";
import { useState } from "react";

import { ListeRapports } from "@/components/rapports/ListeRapports";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Button } from "@/components/ui/button";
import {
  chargerMesRapports,
  creerRapport,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  type ModeleRapport,
} from "@/lib/api/client";
import { MODELES } from "@/lib/rapports";

type Onglet = "miens" | "club";

export const Route = createFileRoute("/_connecte/rapports/")({
  gcTime: 0,
  beforeLoad: ({ context }) => {
    if (context.moi.role === "admin") throw redirect({ to: "/admin" });
  },
  validateSearch: (search: Record<string, unknown>): { onglet?: Onglet | undefined } =>
    search["onglet"] === "club" ? { onglet: "club" } : {},
  loader: async () => {
    try {
      return { mes: await chargerMesRapports(), refus: null };
    } catch (e) {
      // Un élève qui n'est pas président, un encadreur non vérifié ou sans club : la page l'explique.
      if (e instanceof ErreurApi && (e.statut === 403 || e.statut === 404))
        return { mes: null, refus: e.message };
      throw e;
    }
  },
  head: () => ({
    meta: [
      { title: "Rapports d'activité — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: Rapports,
});

// « Mes rapports » (spec 038) : mes brouillons et rapports, et ceux du club que je reçois.
function Rapports() {
  const { mes, refus } = Route.useLoaderData();
  const { onglet = "miens" } = Route.useSearch();
  const navigate = useNavigate();
  const [erreur, setErreur] = useState<string | null>(null);
  const miens = mes?.rapports.filter((r) => r.mien) ?? [];
  const duClub = mes?.rapports.filter((r) => !r.mien) ?? [];

  const nouveau = async (modele: ModeleRapport) => {
    setErreur(null);
    try {
      const rapport = await creerRapport(modele);
      await navigate({ to: "/rapports/$id", params: { id: rapport.id } });
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    }
  };

  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-3xl">
        <Link
          to="/mon-espace"
          className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> Mon espace
        </Link>
        <p className="mt-4 flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
          <span className="h-1 w-8 rounded-full bg-primary" />
          Documenter
        </p>
        <h1 className="mt-3 text-4xl leading-tight md:text-5xl">
          <span className="text-logo-blue">Rapports</span>{" "}
          <span className="text-primary">d'activité</span>
        </h1>

        {refus || !mes ? (
          <p className="mt-8 rounded-3xl bg-card p-6 shadow-card">{refus}</p>
        ) : (
          <>
            <p className="mt-4 max-w-2xl text-muted-foreground">
              Chaque rapport de {mes.club.nom} est reçu par les encadreurs du club, puis examiné par
              l'équipe. Les points arrivent à l'approbation ; rien n'est publié sur le site.
            </p>
            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              {mes.modeles.map((modele) => (
                <Button
                  key={modele}
                  variant="outline"
                  onClick={() => nouveau(modele)}
                  className="h-auto flex-col items-start gap-1 whitespace-normal rounded-3xl bg-card p-4 text-left shadow-card"
                >
                  <span className="inline-flex items-center gap-2 font-bold text-logo-blue">
                    <Plus className="size-4" /> {MODELES[modele].libelle}
                  </span>
                  <span className="text-xs font-medium text-muted-foreground">
                    {MODELES[modele].aide}
                  </span>
                </Button>
              ))}
            </div>
            {erreur && (
              <p role="alert" className="mt-3 font-semibold text-logo-red">
                {erreur}
              </p>
            )}

            <div role="tablist" className="mt-8 flex gap-2">
              {(
                [
                  ["miens", `Mes rapports (${miens.length})`],
                  ["club", `Rapports du club (${duClub.length})`],
                ] as const
              ).map(([code, libelle]) => (
                <Link
                  key={code}
                  role="tab"
                  aria-selected={onglet === code}
                  to="/rapports"
                  search={code === "club" ? { onglet: "club" } : {}}
                  className={`rounded-full px-4 py-2 text-sm font-bold ${onglet === code ? "bg-primary text-primary-foreground" : "bg-card text-ink ring-1 ring-border"}`}
                >
                  {libelle}
                </Link>
              ))}
            </div>
            <div className="mt-4">
              {onglet === "club" ? (
                <ListeRapports
                  rapports={duClub}
                  vide="Aucun rapport des autres responsables du club pour l'instant."
                />
              ) : (
                <ListeRapports rapports={miens} vide="Tu n'as encore déposé aucun rapport." />
              )}
            </div>
          </>
        )}
      </div>
    </main>
  );
}
