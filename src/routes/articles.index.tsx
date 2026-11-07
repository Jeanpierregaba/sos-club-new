import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, Newspaper, PenLine } from "lucide-react";

import { Couverture } from "@/components/articles/Galerie";
import { DecorAnime } from "@/components/DecorAnime";
import { FilAriane } from "@/components/FilAriane";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteMotion } from "@/components/SiteMotion";
import { chargerArticles, chargerAxes } from "@/lib/api/client";
import { signer } from "@/lib/articles";
import { dateCourte } from "@/lib/dates";

type Recherche = { page?: number; axe?: string };

export const Route = createFileRoute("/articles/")({
  validateSearch: (search: Record<string, unknown>): Recherche => {
    const page = Number(search["page"]);
    const axe = typeof search["axe"] === "string" ? search["axe"] : undefined;
    return {
      ...(Number.isInteger(page) && page > 1 ? { page } : {}),
      ...(axe ? { axe } : {}),
    };
  },
  loaderDeps: ({ search }) => search,
  loader: async ({ deps }) => {
    const [articles, axes] = await Promise.all([
      chargerArticles(deps),
      chargerAxes().catch(() => []),
    ]);
    return { articles, axes };
  },
  head: () => ({
    meta: [
      { title: "Articles des Clubs Santé — Club Santé SOS Docteur TV" },
      {
        name: "description",
        content:
          "Les articles des élèves et des encadreurs des Clubs Santé, relus par l'équipe nationale avant leur publication.",
      },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: Articles,
});

function Articles() {
  const { articles, axes } = Route.useLoaderData();
  const { axe } = Route.useSearch();

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteMotion />
      <SiteHeader />

      <section className="relative isolate overflow-hidden bg-linear-to-br from-mist via-white to-lilac">
        <DecorAnime ton="clair" />
        <div className="mx-auto max-w-7xl px-5 pb-14 pt-8 md:pt-12">
          <FilAriane rubrique="Actualités" page="Articles" />
          <div data-reveal className="max-w-3xl pt-10">
            <span className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-1.5 text-xs font-extrabold uppercase tracking-wide text-logo-red shadow-sm">
              <Newspaper className="size-4" /> Écrits par les clubs
            </span>
            <h1 className="mt-5 text-5xl leading-[0.95] md:text-6xl">
              <span className="text-logo-blue">Les articles</span>{" "}
              <span className="text-primary">des Clubs Santé</span>
            </h1>
            <p className="mt-5 max-w-2xl text-lg font-medium text-ink/75">
              Actions de terrain, conseils de santé, coups de cœur : les élèves et les encadreurs
              racontent. Chaque article est relu par l'équipe nationale avant sa publication.
            </p>
            <Link
              to="/mes-articles"
              className="btn-fx mt-7 inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 font-bold text-primary-foreground shadow-card"
            >
              <PenLine className="size-4" /> Écrire un article
            </Link>
          </div>
        </div>
      </section>

      <section id="articles" className="mx-auto max-w-5xl px-5 py-12">
        {axes.length > 0 && (
          <nav aria-label="Filtrer par axe" className="flex flex-wrap gap-2">
            <Filtre actif={!axe} libelle="Tous les axes" />
            {axes.map((a) => (
              <Filtre key={a.code} actif={axe === a.code} libelle={a.libelle} axe={a.code} />
            ))}
          </nav>
        )}

        {articles.articles.length === 0 ? (
          <div className="mt-8 rounded-3xl bg-card p-10 text-center shadow-card">
            <Newspaper className="mx-auto size-10 text-logo-blue/40" />
            <p className="mt-3 font-semibold">
              Aucun article publié {axe ? "dans cet axe " : ""}pour le moment.
            </p>
            <p className="text-sm text-muted-foreground">Et si le premier était le tien ?</p>
          </div>
        ) : (
          <ul className="mt-8 grid gap-5 md:grid-cols-2">
            {articles.articles.map((a, i) => (
              <li key={a.adresse} data-reveal style={{ "--delay": `${(i % 2) * 80}ms` } as never}>
                <Link
                  to="/articles/$adresse"
                  params={{ adresse: a.adresse }}
                  className="group flex h-full flex-col overflow-hidden rounded-3xl bg-card p-6 shadow-card transition hover:-translate-y-1"
                >
                  {a.couverture && (
                    <Couverture
                      adresse={a.adresse}
                      photo={a.couverture}
                      taille="vignette"
                      className="-mx-6 -mt-6 mb-5 aspect-[16/9] max-w-none !w-[calc(100%+3rem)]"
                    />
                  )}
                  <span className="self-start rounded-full bg-mist px-3 py-1 text-xs font-bold text-logo-blue">
                    {a.axe.libelle}
                  </span>
                  <h2 className="mt-3 font-display text-2xl leading-tight text-ink">{a.titre}</h2>
                  <p className="mt-2 line-clamp-3 text-ink/75">{a.chapo}</p>
                  <p className="mt-auto flex items-center justify-between gap-3 pt-5 text-sm text-muted-foreground">
                    <span>
                      {signer(a.signature)} · {dateCourte(a.publie_le)}
                    </span>
                    <ArrowRight className="size-4 shrink-0 text-primary transition group-hover:translate-x-1" />
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        )}

        {articles.pages > 1 && (
          <nav aria-label="Pages" className="mt-10 flex items-center justify-center gap-3">
            {articles.page > 1 && (
              <Link
                to="/articles"
                search={{
                  ...(axe ? { axe } : {}),
                  ...(articles.page > 2 ? { page: articles.page - 1 } : {}),
                }}
                className="rounded-full bg-white px-5 py-2 font-bold text-logo-blue shadow-sm"
              >
                Plus récents
              </Link>
            )}
            <span className="text-sm text-muted-foreground">
              Page {articles.page} sur {articles.pages}
            </span>
            {articles.page < articles.pages && (
              <Link
                to="/articles"
                search={{ ...(axe ? { axe } : {}), page: articles.page + 1 }}
                className="rounded-full bg-white px-5 py-2 font-bold text-logo-blue shadow-sm"
              >
                Plus anciens
              </Link>
            )}
          </nav>
        )}
      </section>

      <SiteFooter />
    </div>
  );
}

function Filtre({ actif, libelle, axe }: { actif: boolean; libelle: string; axe?: string }) {
  return (
    <Link
      to="/articles"
      search={axe ? { axe } : {}}
      aria-current={actif ? "page" : undefined}
      className={`rounded-full px-4 py-2 text-sm font-bold transition ${actif ? "bg-logo-blue text-white" : "bg-white text-logo-blue shadow-sm hover:bg-mist"}`}
    >
      {libelle}
    </Link>
  );
}
