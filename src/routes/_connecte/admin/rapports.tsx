import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight, Download, FileDown } from "lucide-react";

import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { EtatRapport } from "@/components/rapports/EtatRapport";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { peut } from "@/lib/admin";
import {
  adminArchiveRapports,
  urlExportRapports,
  urlPdfRapportAdmin,
  type FiltresArchive,
  type ModeleRapport,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";
import { ETATS_RAPPORT, MODELES } from "@/lib/rapports";

const ETATS = ["soumis", "a_corriger", "approuve", "refuse"] as const;

export const Route = createFileRoute("/_connecte/admin/rapports")({
  validateSearch: (s: Record<string, unknown>): FiltresArchive => ({
    ...(typeof s["modele"] === "string" && s["modele"] in MODELES
      ? { modele: s["modele"] as ModeleRapport }
      : {}),
    ...(ETATS.includes(s["etat"] as (typeof ETATS)[number])
      ? { etat: s["etat"] as (typeof ETATS)[number] }
      : {}),
    ...(typeof s["recherche"] === "string" && s["recherche"].trim()
      ? { recherche: s["recherche"].slice(0, 100) }
      : {}),
    ...(Number(s["page"]) > 1 ? { page: Number(s["page"]) } : {}),
  }),
  loaderDeps: ({ search }) => search,
  loader: ({ deps }) => adminArchiveRapports(deps),
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Archive,
});

const CHAMP =
  "h-10 rounded-full border bg-white px-4 text-sm font-semibold outline-none focus:border-logo-blue";

// L'archive des rapports (spec 038) : tous les rapports soumis du périmètre, leurs points et leurs doublons. Les
// décisions se prennent dans la file de modération ; ici, on cherche et on exporte.
function Archive() {
  const archive = Route.useLoaderData();
  const recherche = Route.useSearch();
  const { admin } = Route.useRouteContext();
  const naviguer = useNavigate({ from: Route.fullPath });
  const filtrer = (changement: Partial<FiltresArchive>) =>
    naviguer({ search: (avant) => ({ ...avant, ...changement, page: undefined }) });
  const pages = Math.max(1, Math.ceil(archive.total / archive.par_page));
  const page = recherche.page ?? 1;

  return (
    <div className="space-y-6">
      <EnTeteAdmin sur="Clubs" bleu="Rapports" vert="d'activité">
        Les rapports soumis par les encadreurs et les présidents, privés. Les noms d'élèves ne
        figurent nulle part ; l'export est journalisé.
      </EnTeteAdmin>

      <div className="flex flex-wrap items-center gap-2">
        <input
          type="search"
          aria-label="Référence ou club"
          placeholder="Référence ou club"
          defaultValue={recherche.recherche ?? ""}
          onKeyDown={(e) => {
            if (e.key === "Enter") filtrer({ recherche: e.currentTarget.value || undefined });
          }}
          className={CHAMP}
        />
        <select
          aria-label="Modèle"
          value={recherche.modele ?? ""}
          onChange={(e) => filtrer({ modele: (e.target.value || undefined) as ModeleRapport })}
          className={CHAMP}
        >
          <option value="">Tous les modèles</option>
          {Object.entries(MODELES).map(([code, m]) => (
            <option key={code} value={code}>
              {m.libelle}
            </option>
          ))}
        </select>
        <select
          aria-label="État"
          value={recherche.etat ?? ""}
          onChange={(e) =>
            filtrer({ etat: (e.target.value || undefined) as FiltresArchive["etat"] })
          }
          className={CHAMP}
        >
          <option value="">Tous les états</option>
          {ETATS.map((etat) => (
            <option key={etat} value={etat}>
              {ETATS_RAPPORT[etat].libelle}
            </option>
          ))}
        </select>
        {peut(admin, "rapports", "exporter") && (
          <a
            href={urlExportRapports(recherche)}
            download
            className="inline-flex h-10 items-center gap-2 rounded-full bg-primary px-4 text-sm font-bold text-primary-foreground"
          >
            <Download className="size-4" /> Exporter en CSV
          </a>
        )}
      </div>

      <p className="text-sm font-semibold text-muted-foreground">
        {archive.total} rapport{archive.total > 1 ? "s" : ""}
      </p>
      {archive.rapports.length === 0 ? (
        <p className="rounded-3xl border border-dashed p-8 text-center font-semibold text-muted-foreground">
          Aucun rapport ne correspond à ces filtres.
        </p>
      ) : (
        <ul className="divide-y overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-border">
          {archive.rapports.map((r) => (
            <li key={r.id} className="flex flex-wrap items-start gap-3 px-4 py-3 sm:px-5">
              <div className="min-w-0 flex-1">
                <p className="text-xs font-extrabold uppercase tracking-wider text-logo-blue">
                  {r.reference} · {MODELES[r.modele].libelle}
                  {r.type_activite && ` · ${r.type_activite}`}
                </p>
                <p className="break-words font-bold text-ink">{r.titre}</p>
                <p className="break-words text-xs font-semibold text-muted-foreground">
                  {r.club.nom} · {r.dre} · {r.auteur}
                  {r.periode && ` · ${r.periode}`}
                  {r.soumis_le && ` · soumis le ${dateCourte(r.soumis_le)}`}
                  {r.doublon_de && ` · doublon de ${r.doublon_de}`}
                </p>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1 text-sm">
                <EtatRapport etat={r.etat} />
                {(r.points_auteur !== null || r.points_club !== null) && (
                  <span className="font-bold text-ink">
                    {r.points_auteur !== null && `+${r.points_auteur} encadreur`}
                    {r.points_auteur !== null && r.points_club !== null && " · "}
                    {r.points_club !== null && `+${r.points_club} club`}
                  </span>
                )}
                {r.etat === "approuve" && (
                  <a
                    href={urlPdfRapportAdmin(r.id)}
                    download
                    aria-label={`Télécharger le PDF de ${r.reference}`}
                    className="inline-flex items-center gap-1 font-bold text-logo-blue hover:underline"
                  >
                    <FileDown className="size-4" /> PDF
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {pages > 1 && (
        <nav className="flex items-center justify-center gap-3" aria-label="Pages">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => naviguer({ search: (avant) => ({ ...avant, page: page - 1 }) })}
            className="rounded-full p-2 ring-1 ring-border disabled:opacity-40"
            aria-label="Page précédente"
          >
            <ChevronLeft className="size-4" />
          </button>
          <span className="text-sm font-bold">
            {page} / {pages}
          </span>
          <button
            type="button"
            disabled={page >= pages}
            onClick={() => naviguer({ search: (avant) => ({ ...avant, page: page + 1 }) })}
            className="rounded-full p-2 ring-1 ring-border disabled:opacity-40"
            aria-label="Page suivante"
          >
            <ChevronRight className="size-4" />
          </button>
        </nav>
      )}
    </div>
  );
}
