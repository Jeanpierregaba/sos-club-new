import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight, Lock } from "lucide-react";

import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { ACTIONS_JOURNAL, dateHeure } from "@/lib/admin";
import { chargerJournal } from "@/lib/api/client";

type Recherche = {
  auteur?: string | undefined;
  action?: string | undefined;
  depuis?: string | undefined;
  avant?: string | undefined;
  page?: number | undefined;
};

export const Route = createFileRoute("/_connecte/admin/journal")({
  validateSearch: (s: Record<string, unknown>): Recherche => ({
    ...(typeof s["auteur"] === "string" && /^[0-9a-f-]{36}$/.test(s["auteur"])
      ? { auteur: s["auteur"] }
      : {}),
    ...(typeof s["action"] === "string" && s["action"] ? { action: s["action"] } : {}),
    ...(typeof s["depuis"] === "string" && s["depuis"] ? { depuis: s["depuis"] } : {}),
    ...(typeof s["avant"] === "string" && s["avant"] ? { avant: s["avant"] } : {}),
    ...(Number(s["page"]) > 1 ? { page: Number(s["page"]) } : {}),
  }),
  loaderDeps: ({ search }) => search,
  loader: ({ deps }) =>
    chargerJournal({
      auteur: deps.auteur,
      action: deps.action,
      // Les dates du formulaire sont des jours : « avant » inclut tout le jour choisi.
      depuis: deps.depuis ? `${deps.depuis}T00:00:00Z` : undefined,
      avant: deps.avant ? `${deps.avant}T23:59:59Z` : undefined,
      page: deps.page,
    }),
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Journal,
});

const CHAMP =
  "h-10 rounded-full border bg-white px-4 text-sm font-semibold outline-none focus:border-logo-blue";

function Journal() {
  const journal = Route.useLoaderData();
  const recherche = Route.useSearch();
  const naviguer = useNavigate({ from: Route.fullPath });
  const filtrer = (changement: Partial<Recherche>) =>
    naviguer({ search: (avant) => ({ ...avant, ...changement, page: undefined }) });
  const pages = Math.max(1, Math.ceil(journal.total / journal.par_page));

  return (
    <div className="space-y-6">
      <EnTeteAdmin sur="Traçabilité" bleu="Journal" vert="d'audit">
        <span className="inline-flex items-center gap-1.5">
          <Lock className="size-4" /> Chaque opération sensible, avec son auteur et sa date. Aucune
          entrée ne peut être modifiée ni supprimée.
        </span>
      </EnTeteAdmin>

      <div className="flex flex-wrap gap-2">
        <label className="sr-only" htmlFor="filtre-action">
          Action
        </label>
        <select
          id="filtre-action"
          value={recherche.action ?? ""}
          onChange={(e) => filtrer({ action: e.target.value || undefined })}
          className={CHAMP}
        >
          <option value="">Toutes les actions</option>
          {Object.entries(ACTIONS_JOURNAL).map(([cle, libelle]) => (
            <option key={cle} value={cle}>
              {libelle}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm font-semibold">
          Du
          <input
            type="date"
            value={recherche.depuis ?? ""}
            onChange={(e) => filtrer({ depuis: e.target.value || undefined })}
            className={CHAMP}
          />
        </label>
        <label className="flex items-center gap-2 text-sm font-semibold">
          au
          <input
            type="date"
            value={recherche.avant ?? ""}
            onChange={(e) => filtrer({ avant: e.target.value || undefined })}
            className={CHAMP}
          />
        </label>
      </div>

      {recherche.auteur && (
        <p className="flex flex-wrap items-center gap-2 text-sm font-semibold">
          Opérations de {journal.evenements[0]?.auteur_libelle ?? "cet auteur"}
          <button
            type="button"
            onClick={() => filtrer({ auteur: undefined })}
            className="rounded-full bg-white px-3 py-1 text-xs font-bold ring-1 ring-border hover:ring-night/30"
          >
            Voir tous les auteurs
          </button>
        </p>
      )}

      <div className="overflow-x-auto rounded-3xl bg-white shadow-sm ring-1 ring-border">
        <table className="w-full min-w-[44rem] text-sm">
          <thead className="bg-mist-soft text-left text-[11px] font-extrabold uppercase tracking-wider text-ink/70">
            <tr>
              <th scope="col" className="px-4 py-3">
                Date (UTC)
              </th>
              <th scope="col" className="px-4 py-3">
                Action
              </th>
              <th scope="col" className="px-4 py-3">
                Auteur
              </th>
              <th scope="col" className="px-4 py-3">
                Détails
              </th>
            </tr>
          </thead>
          <tbody>
            {journal.evenements.map((e) => (
              <tr key={e.id} className="border-t align-top">
                <td className="whitespace-nowrap px-4 py-3 font-semibold text-muted-foreground">
                  {dateHeure(e.quand)}
                </td>
                <td className="px-4 py-3 font-bold">{ACTIONS_JOURNAL[e.action] ?? e.action}</td>
                <td className="px-4 py-3">
                  {e.auteur_id && !recherche.auteur ? (
                    <button
                      type="button"
                      onClick={() => filtrer({ auteur: e.auteur_id ?? undefined })}
                      title="Voir toutes ses opérations"
                      className="text-left font-semibold text-logo-blue hover:underline"
                    >
                      {e.auteur_libelle ?? "—"}
                    </button>
                  ) : (
                    (e.auteur_libelle ?? "—")
                  )}
                </td>
                <td className="px-4 py-3 text-xs text-muted-foreground">
                  <Details details={e.details} perimetre={e.perimetre} />
                </td>
              </tr>
            ))}
            {journal.evenements.length === 0 && (
              <tr>
                <td
                  colSpan={4}
                  className="px-4 py-10 text-center font-semibold text-muted-foreground"
                >
                  Aucune opération pour ces filtres.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between gap-3 text-sm font-semibold">
        <span className="text-muted-foreground">
          {journal.total} opération{journal.total > 1 ? "s" : ""}
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={journal.page <= 1}
            onClick={() => naviguer({ search: (a) => ({ ...a, page: journal.page - 1 }) })}
            aria-label="Page précédente"
            className="inline-flex size-9 items-center justify-center rounded-full border bg-white disabled:opacity-40"
          >
            <ChevronLeft className="size-4" />
          </button>
          <span>
            {journal.page} / {pages}
          </span>
          <button
            type="button"
            disabled={journal.page >= pages}
            onClick={() => naviguer({ search: (a) => ({ ...a, page: journal.page + 1 }) })}
            aria-label="Page suivante"
            className="inline-flex size-9 items-center justify-center rounded-full border bg-white disabled:opacity-40"
          >
            <ChevronRight className="size-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

function Details({
  details,
  perimetre,
}: {
  details: Record<string, unknown>;
  perimetre: string | null;
}) {
  const lignes = Object.entries(details).filter(
    ([, v]) => v !== null && v !== "" && !(Array.isArray(v) && !v.length),
  );
  if (!lignes.length && !perimetre) return <>—</>;
  return (
    <dl className="grid gap-0.5">
      {perimetre && (
        <div className="flex gap-1">
          <dt className="font-bold">Périmètre :</dt>
          <dd>{perimetre}</dd>
        </div>
      )}
      {lignes.map(([cle, valeur]) => (
        <div key={cle} className="flex gap-1">
          <dt className="font-bold">{cle.replaceAll("_", " ")} :</dt>
          <dd className="break-all">
            {Array.isArray(valeur)
              ? valeur.join(", ")
              : typeof valeur === "object"
                ? JSON.stringify(valeur)
                : String(valeur)}
          </dd>
        </div>
      ))}
    </dl>
  );
}
