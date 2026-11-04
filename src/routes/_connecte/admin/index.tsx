import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, CalendarX, Clock, Download, UserPlus, Users } from "lucide-react";

import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import {
  ACTIONS_JOURNAL,
  PROFILS,
  dateHeure,
  peut,
  peutExporter,
  peutVoirInscrits,
} from "@/lib/admin";
import { chargerTableauDeBord, ErreurApi } from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/admin/")({
  // Sans le droit, pas d'erreur : le tableau de bord se réduit aux raccourcis.
  loader: async () => {
    try {
      return await chargerTableauDeBord();
    } catch (erreur) {
      if (erreur instanceof ErreurApi && erreur.statut === 403) return null;
      throw erreur;
    }
  },
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: TableauDeBordPage,
});

const nombre = (n: number) => String(n).replace(/\B(?=(\d{3})+$)/g, " ");

function TableauDeBordPage() {
  const { admin } = Route.useRouteContext();
  const tableau = Route.useLoaderData();

  const raccourcis = [
    {
      to: "/admin/collaborateurs",
      libelle: "Inviter un collaborateur",
      i: UserPlus,
      visible: admin.super_admin,
    },
    {
      to: "/admin/inscrits",
      libelle: "Chercher un inscrit",
      i: Users,
      visible: peutVoirInscrits(admin),
    },
    { to: "/admin/exports", libelle: "Exporter", i: Download, visible: peutExporter(admin) },
  ].filter((r) => r.visible);

  return (
    <div className="space-y-8">
      <EnTeteAdmin sur="Tableau de bord national" bleu={`Bonjour`} vert={`${admin.prenom} !`}>
        {tableau ? (
          <span className="inline-flex items-center gap-1.5">
            <Clock className="size-4" /> Chiffres calculés le {dateHeure(tableau.calcule_le)} (UTC)
          </span>
        ) : (
          "Ton profil n'a pas accès aux indicateurs : voici tes raccourcis."
        )}
      </EnTeteAdmin>

      {raccourcis.length > 0 && (
        <ul className="grid gap-3 sm:grid-cols-3">
          {raccourcis.map(({ to, libelle, i: Icone }) => (
            <li key={to}>
              <Link
                to={to}
                className="card-fx group flex items-center gap-3 rounded-2xl bg-white p-4 font-bold shadow-sm ring-1 ring-border"
              >
                <span className="inline-flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <Icone className="size-5" />
                </span>
                <span className="flex-1">{libelle}</span>
                <ArrowRight className="size-4 text-ink/40 transition group-hover:translate-x-1" />
              </Link>
            </li>
          ))}
        </ul>
      )}

      {tableau && (
        <>
          {tableau.semestre_en_cours === null && (
            <p
              role="status"
              className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-2xl bg-sun/25 px-4 py-3 text-sm font-semibold text-ink"
            >
              <CalendarX aria-hidden className="size-4 shrink-0" />
              Aucun semestre en cours : les points gagnés aujourd'hui ne comptent dans aucun
              classement de semestre.
              {peut(admin, "points", "consulter") && (
                <Link to="/admin/points" className="font-bold text-logo-blue underline">
                  Gérer les semestres
                </Link>
              )}
            </p>
          )}
          <section aria-labelledby="titre-comptes">
            <h2 id="titre-comptes" className="text-xl text-logo-blue">
              Comptes
            </h2>
            <dl className="mt-3 grid gap-3 sm:grid-cols-3">
              {(["eleve", "encadreur", "admin"] as const).map((profil) => (
                <div
                  key={profil}
                  className="flex flex-col-reverse rounded-2xl bg-white p-5 shadow-sm ring-1 ring-border"
                >
                  <dt className="mt-1 text-sm font-bold text-muted-foreground">
                    {PROFILS[profil]}s
                  </dt>
                  <dd className="font-display text-4xl text-logo-blue">
                    {nombre(tableau.comptes_par_profil[profil] ?? 0)}
                  </dd>
                </div>
              ))}
            </dl>
            <p className="mt-2 text-sm font-semibold text-muted-foreground">
              Dont {nombre(tableau.comptes_par_statut["suspendu"] ?? 0)} suspendu(s) et{" "}
              {nombre(tableau.comptes_par_statut["revoque"] ?? 0)} révoqué(s).
            </p>
          </section>

          <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
            <section
              aria-labelledby="titre-inscriptions"
              className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-border sm:p-6"
            >
              <h2 id="titre-inscriptions" className="text-xl text-logo-blue">
                Inscriptions des 30 derniers jours
              </h2>
              <Barres jours={tableau.inscriptions_30_jours} />
            </section>

            <section aria-labelledby="titre-indicateurs" className="space-y-3">
              <h2 id="titre-indicateurs" className="text-xl text-logo-blue">
                Indicateurs
              </h2>
              <ul className="grid gap-2">
                {tableau.indicateurs.map((indicateur) => (
                  <li
                    key={indicateur.id}
                    className={`flex items-center justify-between gap-3 rounded-2xl p-4 ${
                      indicateur.valeur === null
                        ? "border-2 border-dashed border-border bg-transparent"
                        : "bg-white shadow-sm ring-1 ring-border"
                    }`}
                  >
                    <span className="text-sm font-bold">{indicateur.libelle}</span>
                    {indicateur.valeur === null ? (
                      <span className="text-right text-xs font-semibold text-muted-foreground">
                        Disponible avec le module
                        <br />« {indicateur.disponible_avec} »
                      </span>
                    ) : (
                      <span className="font-display text-2xl text-primary">
                        {nombre(indicateur.valeur)}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          </div>

          {tableau.derniers_evenements && (
            <section
              aria-labelledby="titre-journal"
              className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-border sm:p-6"
            >
              <div className="flex items-center justify-between gap-3">
                <h2 id="titre-journal" className="text-xl text-logo-blue">
                  Dernières opérations
                </h2>
                {peut(admin, "journal", "consulter") && (
                  <Link
                    to="/admin/journal"
                    className="text-sm font-bold text-logo-blue hover:underline"
                  >
                    Tout le journal
                  </Link>
                )}
              </div>
              <ul className="mt-3 divide-y">
                {tableau.derniers_evenements.map((e) => (
                  <li
                    key={e.id}
                    className="flex flex-wrap items-baseline justify-between gap-2 py-2.5"
                  >
                    <span className="text-sm">
                      <strong>{ACTIONS_JOURNAL[e.action] ?? e.action}</strong>
                      {e.auteur_libelle && (
                        <span className="text-muted-foreground"> · {e.auteur_libelle}</span>
                      )}
                    </span>
                    <span className="text-xs font-semibold text-muted-foreground">
                      {dateHeure(e.quand)}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}
    </div>
  );
}

// Un histogramme léger, en CSS : une barre par jour, la valeur au survol et pour les lecteurs d'écran.
function Barres({ jours }: { jours: [string, number][] }) {
  const max = Math.max(1, ...jours.map(([, n]) => n));
  const total = jours.reduce((s, [, n]) => s + n, 0);
  return (
    <div className="mt-4">
      <p className="text-sm font-semibold text-muted-foreground">
        {nombre(total)} inscription{total > 1 ? "s" : ""} sur la période
      </p>
      <ol className="mt-4 flex h-40 items-end gap-1" aria-label="Inscriptions par jour">
        {jours.map(([jour, n]) => (
          <li key={jour} className="group relative flex h-full flex-1 items-end">
            <span
              className="w-full rounded-t-md bg-primary/80 transition group-hover:bg-logo-blue"
              style={{ height: `${Math.max(n ? 6 : 2, (n / max) * 100)}%`, opacity: n ? 1 : 0.25 }}
            />
            <span className="sr-only">
              {jour} : {n}
            </span>
            <span
              aria-hidden
              className="pointer-events-none absolute -top-7 left-1/2 hidden -translate-x-1/2 whitespace-nowrap rounded-md bg-night px-1.5 py-0.5 text-[10px] font-bold text-white group-hover:block"
            >
              {jour.slice(5)} · {n}
            </span>
          </li>
        ))}
      </ol>
      <div className="mt-1 flex justify-between text-[11px] font-semibold text-muted-foreground">
        <span>{jours[0]?.[0].slice(5)}</span>
        <span>{jours.at(-1)?.[0].slice(5)}</span>
      </div>
    </div>
  );
}
