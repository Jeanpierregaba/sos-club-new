import { createFileRoute, redirect } from "@tanstack/react-router";

import { Editeur } from "@/components/articles/Editeur";
import { PageArticle } from "@/components/articles/PageArticle";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { chargerAxes, chargerMonArticle } from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/mes-articles/$id")({
  gcTime: 0,
  beforeLoad: ({ context }) => {
    if (context.moi.role === "admin") throw redirect({ to: "/admin" });
  },
  loader: async ({ params }) => {
    const [article, axes] = await Promise.all([chargerMonArticle(params.id), chargerAxes()]);
    return { article, axes };
  },
  head: () => ({
    meta: [
      { title: "Mon article — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: MonArticle,
});

function MonArticle() {
  const { article, axes } = Route.useLoaderData();
  const { moi } = Route.useRouteContext();
  return (
    <PageArticle titre="Mon" accent="article">
      {/* La clé remonte l'éditeur quand on passe d'un article à un autre. */}
      <Editeur key={article.id} article={article} axes={axes} eleve={moi.role === "eleve"} />
    </PageArticle>
  );
}
