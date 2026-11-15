import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { ArrowLeft, Download } from "lucide-react";

import { ChampsRapport } from "@/components/rapports/ChampsRapport";
import { EtatRapport } from "@/components/rapports/EtatRapport";
import { FormulaireRapport } from "@/components/rapports/FormulaireRapport";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import {
  chargerAxes,
  chargerMesRapports,
  chargerRapport,
  chargerSemestresRapport,
  chargerTypesActivite,
  urlDocumentRapport,
  urlPhotoRapport,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";
import { MODELES } from "@/lib/rapports";

export const Route = createFileRoute("/_connecte/rapports/$id")({
  gcTime: 0,
  beforeLoad: ({ context }) => {
    if (context.moi.role === "admin") throw redirect({ to: "/admin" });
  },
  loader: async ({ params }) => {
    const rapport = await chargerRapport(params.id);
    if (!rapport.modifiable) return { rapport, axes: [], types: [], semestres: [], activites: [] };
    const [axes, types, semestres, mes] = await Promise.all([
      chargerAxes(),
      chargerTypesActivite(),
      chargerSemestresRapport(),
      // Le mensuel rappelle les rapports d'activité du club, sans les recopier.
      rapport.modele === "mensuel" ? chargerMesRapports().catch(() => null) : null,
    ]);
    const activites = mes?.rapports.filter((r) => r.modele === "activite" && r.reference) ?? [];
    return { rapport, axes, types, semestres, activites };
  },
  head: () => ({
    meta: [
      { title: "Rapport — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: Rapport,
});

const DECISIONS: Record<string, string> = {
  approuver: "Approuvé",
  corriger: "Correction demandée",
  refuser: "Refusé",
};

function Rapport() {
  const { rapport, axes, types, semestres, activites } = Route.useLoaderData();
  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <Link
          to="/rapports"
          className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> Rapports
        </Link>
        <header>
          <p className="text-xs font-extrabold uppercase tracking-wider text-logo-blue">
            {MODELES[rapport.modele].libelle}
            {rapport.reference && ` · ${rapport.reference}`} · {rapport.club.nom}
          </p>
          <h1 className="mt-2 break-words font-display text-3xl text-ink md:text-4xl">
            {rapport.titre}
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <EtatRapport etat={rapport.etat} />
            {rapport.periode && <span>{rapport.periode}</span>}
            {!rapport.mien && <span>par {rapport.auteur}</span>}
            {rapport.points !== null && (
              <span className="font-bold text-ink">+{rapport.points} points</span>
            )}
            {rapport.doublon_de && <span>Lié à {rapport.doublon_de} (doublon, sans point)</span>}
          </div>
          {rapport.doublons_probables.length > 0 && rapport.etat !== "approuve" && (
            <p className="mt-3 rounded-2xl bg-sun/25 p-3 text-sm font-semibold ring-1 ring-sun">
              Un rapport du même jour et du même type existe déjà :{" "}
              {rapport.doublons_probables.join(", ")}. L'équipe vérifiera qu'il s'agit bien d'une
              autre activité.
            </p>
          )}
        </header>

        {rapport.historique.length > 0 && (
          <section className="rounded-3xl bg-card p-5 shadow-card">
            <h2 className="font-display text-lg text-logo-blue">Décisions de l'équipe</h2>
            <ul className="mt-2 space-y-1 text-sm">
              {rapport.historique.map((d, i) => (
                <li key={i}>
                  <strong>{DECISIONS[d.decision] ?? d.decision}</strong> le{" "}
                  {dateCourte(d.decide_le)} (version {d.version})
                  {d.motif && <span className="text-muted-foreground"> : {d.motif}</span>}
                </li>
              ))}
            </ul>
          </section>
        )}

        {rapport.modifiable ? (
          <FormulaireRapport
            key={rapport.id}
            rapport={rapport}
            axes={axes}
            types={types}
            semestres={semestres}
            activites={activites}
          />
        ) : (
          <section className="space-y-4 rounded-3xl bg-card p-5 shadow-card">
            <ChampsRapport
              modele={rapport.modele}
              donnees={rapport.donnees}
              documents={rapport.documents}
              urlDocument={(piece) => urlDocumentRapport(rapport.id, piece)}
            />
            {rapport.photos.length > 0 && (
              <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {rapport.photos.map((p) => (
                  <li key={p.id}>
                    <a
                      href={urlPhotoRapport(rapport.id, p.id, "grande")}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <img
                        src={urlPhotoRapport(rapport.id, p.id, "vignette")}
                        alt={p.legende ?? "Photo de l'activité"}
                        className="aspect-[4/3] w-full rounded-xl object-cover"
                        loading="lazy"
                      />
                    </a>
                  </li>
                ))}
              </ul>
            )}
            {rapport.etat === "approuve" && (
              <p className="inline-flex items-center gap-2 text-sm text-muted-foreground">
                <Download className="size-4" /> L'export PDF du rapport arrive avec l'archive.
              </p>
            )}
          </section>
        )}
      </div>
    </main>
  );
}
