import { useQuery } from "@tanstack/react-query";
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { Loader2 } from "lucide-react";

import { BlocActivite } from "@/components/admin/activite/BlocActivite";
import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import {
  chargerBlocActivite,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  urlExportActivite,
  type NomBlocActivite,
  type PeriodeActivite,
} from "@/lib/api/client";

// Spec 051 : le suivi d'activité de la plateforme, réservé au super-administrateur. Chaque bloc se charge à part,
// pour que la page s'affiche au fur et à mesure.
const BLOCS: { bloc: NomBlocActivite; titre: string }[] = [
  { bloc: "audience", titre: "Audience" },
  { bloc: "inscription", titre: "Inscription : clics, entonnoir et abandons" },
  { bloc: "jeux", titre: "Jeux" },
  { bloc: "certification", titre: "Certification" },
  { bloc: "contenus", titre: "Contenus" },
  { bloc: "regions", titre: "Régions et clubs" },
  { bloc: "retention", titre: "Rétention et moments d'usage" },
  { bloc: "erreurs", titre: "Erreurs et recherches" },
];

const DATE = /^\d{4}-\d{2}-\d{2}$/;
const RACCOURCIS = [
  { libelle: "Aujourd'hui", jours: 1 },
  { libelle: "7 jours", jours: 7 },
  { libelle: "30 jours", jours: 30 },
  { libelle: "90 jours", jours: 90 },
];

function jourIso(decalage = 0): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - decalage);
  return d.toISOString().slice(0, 10);
}

export const Route = createFileRoute("/_connecte/admin/activite")({
  validateSearch: (search: Record<string, unknown>): PeriodeActivite => ({
    du: typeof search["du"] === "string" && DATE.test(search["du"]) ? search["du"] : undefined,
    au: typeof search["au"] === "string" && DATE.test(search["au"]) ? search["au"] : undefined,
  }),
  beforeLoad: ({ context }) => {
    if (!context.admin.super_admin) throw redirect({ to: "/admin" });
  },
  head: () => ({ meta: [{ title: "Activité — Admin Club Santé" }] }),
  component: Activite,
});

function Activite() {
  const periode = Route.useSearch();
  const naviguer = useNavigate({ from: Route.fullPath });
  const choisir = (suivante: PeriodeActivite) => void naviguer({ search: suivante, replace: true });

  return (
    <div className="space-y-6">
      <EnTeteAdmin sur="Super-administration" bleu="Suivi" vert="d'activité">
        L'usage de la plateforme, mesuré par le site lui-même : sans cookie, sans service extérieur,
        et sans jamais suivre une personne.
      </EnTeteAdmin>

      <section
        aria-label="Période"
        className="flex flex-wrap items-end gap-3 rounded-3xl bg-white p-4 shadow-sm ring-1 ring-border"
      >
        <div className="flex flex-wrap gap-2">
          {RACCOURCIS.map(({ libelle, jours }) => {
            const actif =
              periode.du === jourIso(jours - 1) && (!periode.au || periode.au === jourIso());
            const parDefaut = !periode.du && !periode.au && jours === 30;
            return (
              <button
                key={jours}
                type="button"
                aria-pressed={actif || parDefaut}
                onClick={() => choisir({ du: jourIso(jours - 1), au: jourIso() })}
                className={`rounded-full px-4 py-2 text-sm font-bold ring-1 ring-border ${
                  actif || parDefaut ? "bg-primary text-primary-foreground" : "hover:bg-mist-soft"
                }`}
              >
                {libelle}
              </button>
            );
          })}
        </div>
        <label className="text-sm font-semibold">
          Du
          <input
            type="date"
            value={periode.du ?? ""}
            max={periode.au ?? jourIso()}
            onChange={(e) => choisir({ ...periode, du: e.target.value || undefined })}
            className="ml-2 rounded-xl border border-input px-3 py-1.5"
          />
        </label>
        <label className="text-sm font-semibold">
          Au
          <input
            type="date"
            value={periode.au ?? ""}
            min={periode.du}
            max={jourIso()}
            onChange={(e) => choisir({ ...periode, au: e.target.value || undefined })}
            className="ml-2 rounded-xl border border-input px-3 py-1.5"
          />
        </label>
      </section>

      {BLOCS.map(({ bloc, titre }) => (
        <ChargementBloc key={bloc} bloc={bloc} titre={titre} periode={periode} />
      ))}
    </div>
  );
}

function ChargementBloc({
  bloc,
  titre,
  periode,
}: {
  bloc: NomBlocActivite;
  titre: string;
  periode: PeriodeActivite;
}) {
  const requete = useQuery({
    queryKey: ["activite", bloc, periode.du, periode.au],
    queryFn: () => chargerBlocActivite(bloc, periode),
    staleTime: 60_000,
  });
  if (requete.isPending) {
    return (
      <section className="flex items-center gap-3 rounded-3xl bg-white p-6 shadow-sm ring-1 ring-border">
        <Loader2 aria-hidden className="size-5 animate-spin text-primary" />
        <span className="font-semibold text-muted-foreground">{titre} : chargement…</span>
      </section>
    );
  }
  if (requete.isError) {
    return (
      <section
        role="alert"
        className="rounded-3xl bg-white p-6 font-semibold shadow-sm ring-1 ring-border"
      >
        {titre} :{" "}
        {requete.error instanceof ErreurApi ? requete.error.message : MESSAGE_INDISPONIBLE}
      </section>
    );
  }
  return (
    <BlocActivite titre={titre} bloc={requete.data} urlExport={urlExportActivite(bloc, periode)} />
  );
}
