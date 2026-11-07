import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";

import { TexteArticle } from "@/components/articles/TexteArticle";
import { FilAriane } from "@/components/FilAriane";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { chargerArticle, ErreurApi } from "@/lib/api/client";
import { signer } from "@/lib/articles";
import { dateCourte } from "@/lib/dates";

export const Route = createFileRoute("/articles/$adresse")({
  loader: async ({ params }) => {
    try {
      return await chargerArticle(params.adresse);
    } catch (e) {
      if (e instanceof ErreurApi && e.statut === 404) throw notFound();
      throw e;
    }
  },
  head: ({ loaderData }) => ({
    meta: loaderData
      ? [
          { title: `${loaderData.titre} — Club Santé SOS Docteur TV` },
          { name: "description", content: loaderData.chapo },
          { property: "og:title", content: loaderData.titre },
        ]
      : [{ title: "Article introuvable — Club Santé SOS Docteur TV" }],
  }),
  errorComponent: ServiceIndisponible,
  notFoundComponent: Introuvable,
  component: Article,
});

function Article() {
  const article = Route.useLoaderData();

  return (
    <div className="min-h-screen overflow-x-clip bg-carnet text-ink">
      <SiteHeader />
      <section className="bg-linear-to-br from-mist via-white to-lilac">
        <div className="mx-auto max-w-3xl px-5 pb-10 pt-8 md:pt-12">
          <FilAriane
            rubrique="Actualités"
            parent={{ t: "Articles", href: "/articles" }}
            page={article.titre}
          />
          <Link
            to="/articles"
            search={{ axe: article.axe.code }}
            className="mt-8 inline-block rounded-full bg-white px-3 py-1 text-xs font-bold text-logo-blue shadow-sm"
          >
            {article.axe.libelle}
          </Link>
          <h1 className="mt-4 text-4xl leading-tight text-logo-blue md:text-5xl">
            {article.titre}
          </h1>
          <p className="mt-4 text-lg font-semibold text-ink/75">{article.chapo}</p>
          <p className="mt-5 text-sm text-muted-foreground">
            Par <strong className="text-ink">{signer(article.signature)}</strong> · publié le{" "}
            {dateCourte(article.publie_le)}
          </p>
        </div>
      </section>
      <article className="mx-auto max-w-3xl px-5 py-10">
        <TexteArticle texte={article.texte} />
        <Link
          to="/articles"
          className="mt-12 inline-flex items-center gap-2 font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> Tous les articles
        </Link>
      </article>
      <SiteFooter />
    </div>
  );
}

function Introuvable() {
  return (
    <div className="min-h-screen bg-carnet text-ink">
      <SiteHeader />
      <main className="mx-auto max-w-xl px-5 py-24 text-center">
        <h1 className="text-4xl text-logo-blue">Article introuvable</h1>
        <p className="mt-3 text-muted-foreground">Cet article n'existe pas ou n'est plus publié.</p>
        <Link
          to="/articles"
          className="btn-fx mt-8 inline-flex rounded-full bg-primary px-6 py-3 font-bold text-primary-foreground"
        >
          Voir tous les articles
        </Link>
      </main>
      <SiteFooter />
    </div>
  );
}
