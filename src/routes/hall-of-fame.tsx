import { createFileRoute, Link, redirect, useNavigate } from "@tanstack/react-router";
import { ArrowRight, CalendarRange, Trophy } from "lucide-react";

import {
  Choix,
  ListeClassement,
  Pagination,
  Podium,
} from "@/components/classements/TableauClassement";
import { FilAriane } from "@/components/FilAriane";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteMotion } from "@/components/SiteMotion";
import {
  chargerClassementPublic,
  chargerDre,
  ErreurApi,
  type CategorieClassement,
  type PeriodeClassement,
} from "@/lib/api/client";
import { CATEGORIES, estCategorie, estPeriode, PERIODES, sousTitre } from "@/lib/classements";
import { dateCourte } from "@/lib/dates";

const PAR_PAGE = 50;

type Recherche = {
  categorie?: CategorieClassement;
  dre?: string;
  periode?: PeriodeClassement;
  page?: number;
};

export const Route = createFileRoute("/hall-of-fame")({
  validateSearch: (search: Record<string, unknown>): Recherche => {
    const dre = typeof search["dre"] === "string" && search["dre"] ? search["dre"] : undefined;
    const page = Number(search["page"]);
    return {
      ...(estCategorie(search["categorie"]) ? { categorie: search["categorie"] } : {}),
      ...(dre ? { dre } : {}),
      ...(estPeriode(search["periode"]) ? { periode: search["periode"] } : {}),
      ...(Number.isInteger(page) && page > 1 ? { page } : {}),
    };
  },
  loaderDeps: ({ search }) => search,
  loader: async ({ deps }) => {
    const [classement, dres] = await Promise.all([
      chargerClassementPublic({
        categorie: deps.categorie ?? "eleves",
        niveau: deps.dre ? "dre" : "national",
        ...(deps.dre ? { dre: deps.dre } : {}),
        periode: deps.periode ?? "semestre",
        page: deps.page ?? 1,
        par_page: PAR_PAGE,
      }).catch((erreur: unknown) => {
        // Une DRE inconnue dans l'adresse (lien ancien ou mal recopié) : on montre le classement national.
        if (deps.dre && erreur instanceof ErreurApi && erreur.statut === 404) {
          const { dre: _dre, page: _page, ...reste } = deps;
          throw redirect({ to: "/hall-of-fame", search: reste });
        }
        throw erreur;
      }),
      chargerDre().catch(() => []),
    ]);
    return { classement, dres };
  },
  head: () => ({
    meta: [
      { title: "Classements — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content:
          "Les classements des élèves, des encadreurs et des Clubs Santé, au niveau national et par DRE, pour le semestre en cours et depuis le début.",
      },
      { property: "og:title", content: "Les classements des Clubs Santé" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: HallOfFame,
});

const MESSAGES_VIDES: Record<CategorieClassement, string> = {
  eleves: "Aucun élève n'a encore de points sur cette période.",
  encadreurs: "Aucun encadreur n'a encore de points sur cette période.",
  clubs: "Aucun Club Santé n'a encore de points sur cette période.",
};

function HallOfFame() {
  const { classement, dres } = Route.useLoaderData();
  const recherche = Route.useSearch();
  const naviguer = useNavigate({ from: Route.fullPath });
  const categorie = recherche.categorie ?? "eleves";
  const periode = recherche.periode ?? "semestre";
  const page = recherche.page ?? 1;

  // Changer un filtre ramène à la première page ; une valeur par défaut disparaît de l'adresse.
  const filtrer = (changements: Recherche) =>
    naviguer({
      search: (avant) => {
        const suite = { ...avant, ...changements };
        if (!("page" in changements)) delete suite.page;
        if (suite.categorie === "eleves") delete suite.categorie;
        if (suite.periode === "semestre") delete suite.periode;
        if (!suite.dre) delete suite.dre;
        if (suite.page === 1) delete suite.page;
        return suite;
      },
    });

  const lignes = classement.lignes.map((ligne, index) => ({
    cle: `${page}-${index}`,
    rang: ligne.rang,
    nom: ligne.nom,
    sousTitre: sousTitre(ligne),
    points: ligne.points,
  }));
  const sansSemestre = periode === "semestre" && !classement.semestre;

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      <section className="relative isolate overflow-hidden bg-[color-mix(in_oklch,var(--sun)_20%,white)]">
        <div className="mx-auto max-w-7xl px-4 pb-12 pt-8 sm:px-5 md:pt-12">
          <FilAriane rubrique="Gamification" page="Classements" />
          <div data-reveal="left" className="pt-10">
            <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
              <span className="h-1 w-8 rounded-full bg-primary" />
              Hall of Fame des Clubs Santé
            </p>
            <h1 className="mt-4 text-5xl leading-[0.95] md:text-7xl">
              <span className="block text-logo-blue">Les classements</span>
              <span className="block text-primary">du réseau</span>
            </h1>
            <p className="mt-6 max-w-2xl text-lg font-medium text-ink/75">
              Élèves, encadreurs et Clubs Santé, au niveau national ou dans ta DRE. Chaque point
              vient d'une action vérifiée : quiz réussis, articles publiés, commentaires approuvés.
            </p>
            <p className="mt-4 flex items-center gap-2 text-sm font-bold text-logo-blue">
              <CalendarRange aria-hidden className="size-4" />
              {classement.semestre
                ? `${classement.semestre.libelle}, du ${dateCourte(classement.semestre.debut)} au ${dateCourte(classement.semestre.fin)}`
                : "Aucun semestre en cours"}
            </p>
          </div>
        </div>
      </section>

      <main className="mx-auto max-w-7xl space-y-6 px-4 py-10 sm:px-5">
        <div className="space-y-3 rounded-3xl bg-white p-4 shadow-sm ring-1 ring-border sm:p-5">
          <Choix
            libelle="Catégorie"
            options={CATEGORIES}
            valeur={categorie}
            choisir={(valeur) => filtrer({ categorie: valeur })}
          />
          <div className="flex flex-wrap items-center gap-3">
            <Choix
              libelle="Période"
              options={PERIODES}
              valeur={periode}
              choisir={(valeur) => filtrer({ periode: valeur })}
            />
            <label className="flex min-w-0 items-center gap-2 text-sm font-bold text-ink">
              Niveau
              <select
                value={recherche.dre ?? ""}
                onChange={(evenement) => filtrer({ dre: evenement.target.value })}
                className="min-w-0 rounded-full border bg-white px-4 py-2 font-semibold"
              >
                <option value="">National</option>
                {dres.map((dre) => (
                  <option key={dre.code} value={dre.code}>
                    DRE {dre.nom}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        {sansSemestre ? (
          <div className="rounded-3xl border border-dashed p-8 text-center">
            <p className="font-display text-2xl text-logo-blue">Aucun semestre en cours</p>
            <p className="mt-2 font-semibold text-muted-foreground">
              Le classement du semestre reprendra à l'ouverture du prochain semestre.
            </p>
            <button
              type="button"
              onClick={() => filtrer({ periode: "historique" })}
              className="mt-4 font-bold text-primary underline-offset-4 hover:underline"
            >
              Voir le total historique
            </button>
          </div>
        ) : lignes.length === 0 ? (
          <div className="rounded-3xl border border-dashed p-8 text-center font-semibold text-muted-foreground">
            <p>{page > 1 ? "Cette page est vide." : MESSAGES_VIDES[categorie]}</p>
            {page > 1 && (
              <button
                type="button"
                onClick={() => filtrer({ page: 1 })}
                className="mt-3 font-bold text-primary underline-offset-4 hover:underline"
              >
                Revenir à la première page
              </button>
            )}
          </div>
        ) : (
          <>
            {page === 1 && <Podium lignes={lignes.slice(0, 3)} />}
            <ListeClassement
              libelle={`Classement des ${CATEGORIES.find((c) => c.valeur === categorie)?.libelle.toLowerCase()}`}
              lignes={page === 1 ? lignes.slice(3) : lignes}
            />
            <Pagination
              page={page}
              total={classement.total}
              parPage={PAR_PAGE}
              allerA={(suivante) => filtrer({ page: suivante })}
            />
          </>
        )}

        <aside className="flex flex-wrap items-center justify-between gap-4 rounded-3xl bg-logo-blue p-6 text-white">
          <p className="flex items-center gap-3 font-bold">
            <Trophy aria-hidden className="size-6 text-sun" />
            Les lauréats du championnat Génie Imhotep ont leur propre Hall of Fame.
          </p>
          <Link
            to="/genie-imhotep/hall-of-fame"
            className="inline-flex items-center gap-2 rounded-full bg-white px-5 py-2.5 font-bold text-logo-blue"
          >
            Hall of Fame du Génie Imhotep <ArrowRight className="size-4" />
          </Link>
        </aside>
      </main>
      <SiteFooter />
    </div>
  );
}
