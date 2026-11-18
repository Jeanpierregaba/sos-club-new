import { createFileRoute, useNavigate, useRouter } from "@tanstack/react-router";
import { Merge, RotateCcw, X } from "lucide-react";
import { useState } from "react";

import { CHAMP_ADMIN } from "@/components/admin/DialogueFormulaire";
import { FusionEtablissements } from "@/components/admin/FusionEtablissements";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { peut } from "@/lib/admin";
import {
  adminDoublons,
  adminEcarterDoublon,
  adminListerDre,
  adminRetablirDoublon,
  ErreurApi,
  type FicheDoublon,
  type PaireProbable,
} from "@/lib/api/client";

const RAISONS: Record<string, string> = {
  meme_nom: "Même nom",
  meme_prononciation: "Même prononciation",
  nom_proche: "Nom proche",
};

type Recherche = { dre?: string | undefined; ecartees?: boolean | undefined };

// Doublons probables d'établissements (spec 042) : on fusionne, ou on écarte une paire distincte.
export const Route = createFileRoute("/_connecte/admin/referentiel/doublons")({
  validateSearch: (s: Record<string, unknown>): Recherche => ({
    ...(typeof s["dre"] === "string" && s["dre"] ? { dre: s["dre"] } : {}),
    ...(s["ecartees"] === true || s["ecartees"] === "true" ? { ecartees: true } : {}),
  }),
  loaderDeps: ({ search }) => search,
  loader: async ({ deps }) => {
    const [page, dres] = await Promise.all([adminDoublons(deps), adminListerDre()]);
    return { page, dres };
  },
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Doublons,
});

const pluriel = (n: number, mot: string) => `${n} ${mot}${n > 1 ? "s" : ""}`;

function Fiche({ fiche }: { fiche: FicheDoublon }) {
  return (
    <div className="min-w-0">
      <p className="font-extrabold break-words">{fiche.nom}</p>
      <p className="text-xs text-muted-foreground">
        {fiche.iesg} · {fiche.prefecture ?? "préfecture non renseignée"} ·{" "}
        {fiche.import_source ? "liste nationale" : "annuaire"}
        {fiche.statut === "propose" && " · proposé"}
      </p>
      <p className="text-xs font-semibold">
        {pluriel(fiche.nb_eleves, "élève")} · {pluriel(fiche.nb_encadreurs, "encadreur")}
        {fiche.club && ` · club ${fiche.club.etat.replace("_", " ")}`}
      </p>
    </div>
  );
}

function Doublons() {
  const { admin } = Route.useRouteContext();
  const { page, dres } = Route.useLoaderData();
  const filtres = Route.useSearch();
  const naviguer = useNavigate({ from: Route.fullPath });
  const router = useRouter();
  const [fusion, setFusion] = useState<PaireProbable | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const modifier = peut(admin, "clubs", "modifier");
  const restantes = Object.values(page.par_dre).reduce((s, n) => s + n, 0);

  const basculer = async (paire: PaireProbable) => {
    setErreur(null);
    try {
      await (paire.ecartee ? adminRetablirDoublon : adminEcarterDoublon)(paire.a.id, paire.b.id);
      await router.invalidate();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : "Le service est indisponible, réessaie.");
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2">
        {dres.length > 1 && (
          <select
            aria-label="DRE"
            value={filtres.dre ?? ""}
            onChange={(e) =>
              naviguer({ search: (avant) => ({ ...avant, dre: e.target.value || undefined }) })
            }
            className={`${CHAMP_ADMIN} max-w-60`}
          >
            <option value="">Toutes les DRE ({restantes})</option>
            {dres.map((d) => (
              <option key={d.code} value={d.code}>
                DRE {d.nom} ({page.par_dre[d.code] ?? 0})
              </option>
            ))}
          </select>
        )}
        <label className="inline-flex h-11 items-center gap-2 rounded-full px-3 text-sm font-semibold ring-1 ring-border">
          <input
            type="checkbox"
            checked={filtres.ecartees ?? false}
            onChange={(e) =>
              naviguer({
                search: (avant) => ({ ...avant, ecartees: e.target.checked || undefined }),
              })
            }
            className="size-4 accent-primary"
          />
          Écartées
        </label>
      </div>

      <p aria-live="polite" className="text-sm font-semibold text-muted-foreground">
        {filtres.ecartees
          ? `${pluriel(page.paires.length, "paire écartée")}`
          : `${pluriel(page.paires.length, "doublon probable")}. Vérifie chaque paire : une annexe, un groupe A et B ou deux localités voisines ne sont pas des doublons.`}
      </p>
      {erreur && (
        <Alert variant="destructive" role="alert">
          <AlertDescription>{erreur}</AlertDescription>
        </Alert>
      )}

      {page.paires.length === 0 ? (
        <p className="rounded-3xl border border-dashed p-8 text-center font-semibold text-muted-foreground">
          {filtres.ecartees
            ? "Aucune paire écartée."
            : `Aucun doublon probable ${filtres.dre || admin.perimetre_dre ? "dans cette DRE" : "pour le moment"}.`}
        </p>
      ) : (
        <ul className="grid gap-3">
          {page.paires.map((p) => (
            <li
              key={`${p.a.id}-${p.b.id}`}
              className="rounded-3xl bg-white p-4 shadow-sm ring-1 ring-border md:p-5"
            >
              <p className="mb-2 text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground">
                {p.raison ? RAISONS[p.raison] : "Plus détectée"} · DRE {p.a.dre}
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                <Fiche fiche={p.a} />
                <Fiche fiche={p.b} />
              </div>
              {modifier && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {!p.ecartee && (
                    <button
                      type="button"
                      onClick={() => setFusion(p)}
                      className="inline-flex items-center gap-1.5 rounded-full bg-primary px-3 py-1.5 text-xs font-bold text-primary-foreground transition hover:bg-primary/90"
                    >
                      <Merge className="size-3.5" /> Fusionner
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => void basculer(p)}
                    className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold ring-1 ring-border transition hover:bg-mist-soft"
                  >
                    {p.ecartee ? (
                      <>
                        <RotateCcw className="size-3.5" /> Rétablir
                      </>
                    ) : (
                      <>
                        <X className="size-3.5" /> Pas un doublon
                      </>
                    )}
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {fusion && (
        <FusionEtablissements
          depart={fusion.a}
          autre={fusion.b}
          fermer={() => setFusion(null)}
          apresFusion={() => router.invalidate()}
        />
      )}
    </div>
  );
}
