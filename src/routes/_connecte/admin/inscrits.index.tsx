import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight, Download, Search } from "lucide-react";
import { useEffect, useState } from "react";

import { BadgeStatut } from "@/components/admin/BadgeStatut";
import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { PROFILS, dateCourte, peutExporter } from "@/lib/admin";
import { listerInscrits } from "@/lib/api/client";

type Recherche = {
  recherche?: string | undefined;
  profil?: "eleve" | "encadreur" | "admin" | "visiteur" | undefined;
  statut?: "actif" | "suspendu" | "revoque" | undefined;
  page?: number | undefined;
};

const PROFILS_VALIDES = ["eleve", "encadreur", "visiteur", "admin"] as const;
const STATUTS_VALIDES = ["actif", "suspendu", "revoque"] as const;

export const Route = createFileRoute("/_connecte/admin/inscrits/")({
  validateSearch: (s: Record<string, unknown>): Recherche => ({
    ...(typeof s["recherche"] === "string" && s["recherche"] ? { recherche: s["recherche"] } : {}),
    ...(PROFILS_VALIDES.includes(s["profil"] as never)
      ? { profil: s["profil"] as Recherche["profil"] }
      : {}),
    ...(STATUTS_VALIDES.includes(s["statut"] as never)
      ? { statut: s["statut"] as Recherche["statut"] }
      : {}),
    ...(Number(s["page"]) > 1 ? { page: Number(s["page"]) } : {}),
  }),
  loaderDeps: ({ search }) => search,
  loader: ({ deps }) => listerInscrits({ ...deps, par_page: 25 }),
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Inscrits,
});

const CHAMP =
  "h-10 rounded-full border bg-white px-4 text-sm font-semibold outline-none focus:border-logo-blue";

function Inscrits() {
  const { admin } = Route.useRouteContext();
  const page = Route.useLoaderData();
  const recherche = Route.useSearch();
  const naviguer = useNavigate({ from: Route.fullPath });
  const rechercheUrl = recherche.recherche ?? "";
  const [texte, setTexte] = useState(rechercheUrl);
  // Vrai seulement après une frappe : un changement d'adresse (bouton Retour) ne relance pas de recherche.
  const [saisi, setSaisi] = useState(false);
  const filtrer = (changement: Partial<Recherche>) =>
    naviguer({ search: (avant) => ({ ...avant, ...changement, page: undefined }) });
  const pages = Math.max(1, Math.ceil(page.total / page.par_page));

  // La recherche part après une courte pause de frappe, pas à chaque lettre.
  useEffect(() => {
    setTexte(rechercheUrl);
    setSaisi(false);
  }, [rechercheUrl]);

  useEffect(() => {
    if (!saisi) return;
    const minuterie = setTimeout(() => {
      setSaisi(false);
      void naviguer({
        search: (avant) => ({ ...avant, recherche: texte.trim() || undefined, page: undefined }),
      });
    }, 350);
    return () => clearTimeout(minuterie);
  }, [texte, saisi, naviguer]);

  return (
    <div className="space-y-6">
      <EnTeteAdmin
        sur="Annuaire"
        bleu="Les inscrits"
        vert="de la plateforme"
        actions={
          peutExporter(admin) && (
            <Link
              to="/admin/exports"
              className="btn-fx inline-flex h-11 items-center gap-2 rounded-full bg-primary px-5 text-sm font-bold text-primary-foreground"
            >
              <Download className="size-4" /> Exporter
            </Link>
          )
        }
      >
        Élèves, encadreurs et collaborateurs. Les filtres par club et par DRE arriveront avec les
        clubs.
      </EnTeteAdmin>

      <div className="flex flex-wrap gap-2">
        <div className="relative min-w-60 flex-1">
          <Search
            aria-hidden
            className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
          />
          <input
            type="search"
            value={texte}
            onChange={(e) => {
              setTexte(e.target.value);
              setSaisi(true);
            }}
            placeholder="Nom, prénom, identifiant ou e-mail"
            aria-label="Rechercher un inscrit"
            className={`${CHAMP} w-full pl-10`}
          />
        </div>
        <select
          aria-label="Profil"
          value={recherche.profil ?? ""}
          onChange={(e) =>
            filtrer({ profil: (e.target.value || undefined) as Recherche["profil"] })
          }
          className={CHAMP}
        >
          <option value="">Tous les profils</option>
          {PROFILS_VALIDES.map((p) => (
            <option key={p} value={p}>
              {PROFILS[p]}
            </option>
          ))}
        </select>
        <select
          aria-label="Statut"
          value={recherche.statut ?? ""}
          onChange={(e) =>
            filtrer({ statut: (e.target.value || undefined) as Recherche["statut"] })
          }
          className={CHAMP}
        >
          <option value="">Tous les statuts</option>
          <option value="actif">Actif</option>
          <option value="suspendu">Suspendu</option>
          <option value="revoque">Révoqué</option>
        </select>
      </div>

      <div className="overflow-x-auto rounded-3xl bg-white shadow-sm ring-1 ring-border">
        <table className="w-full min-w-[40rem] text-sm">
          <thead className="bg-mist-soft text-left text-[11px] font-extrabold uppercase tracking-wider text-ink/70">
            <tr>
              <th scope="col" className="px-4 py-3">
                Nom
              </th>
              <th scope="col" className="px-4 py-3">
                Identifiant
              </th>
              <th scope="col" className="px-4 py-3">
                Profil
              </th>
              <th scope="col" className="px-4 py-3">
                Statut
              </th>
              <th scope="col" className="px-4 py-3">
                Inscription
              </th>
            </tr>
          </thead>
          <tbody>
            {page.inscrits.map((i) => (
              <tr key={i.id} className="border-t hover:bg-mist-soft/60">
                <td className="px-4 py-3 font-bold">
                  <Link
                    to="/admin/inscrits/$id"
                    params={{ id: i.id }}
                    className="text-logo-blue hover:underline"
                  >
                    {i.prenom} {i.nom}
                  </Link>
                  {i.email && (
                    <span className="block text-xs font-medium text-muted-foreground">
                      {i.email}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 font-mono text-xs">{i.identifiant}</td>
                <td className="px-4 py-3">{PROFILS[i.role]}</td>
                <td className="px-4 py-3">
                  <BadgeStatut statut={i.statut} />
                </td>
                <td className="px-4 py-3 text-muted-foreground">{dateCourte(i.cree_le)}</td>
              </tr>
            ))}
            {page.inscrits.length === 0 && (
              <tr>
                <td
                  colSpan={5}
                  className="px-4 py-10 text-center font-semibold text-muted-foreground"
                >
                  Aucun inscrit ne correspond à ces filtres.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between gap-3 text-sm font-semibold">
        <span className="text-muted-foreground">
          {page.total} inscrit{page.total > 1 ? "s" : ""}
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={page.page <= 1}
            onClick={() => naviguer({ search: (a) => ({ ...a, page: page.page - 1 }) })}
            aria-label="Page précédente"
            className="inline-flex size-9 items-center justify-center rounded-full border bg-white disabled:opacity-40"
          >
            <ChevronLeft className="size-4" />
          </button>
          <span>
            {page.page} / {pages}
          </span>
          <button
            type="button"
            disabled={page.page >= pages}
            onClick={() => naviguer({ search: (a) => ({ ...a, page: page.page + 1 }) })}
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
