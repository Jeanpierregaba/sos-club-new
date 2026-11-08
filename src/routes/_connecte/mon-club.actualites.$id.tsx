import { createFileRoute, redirect } from "@tanstack/react-router";

import { Editeur } from "@/components/articles/Editeur";
import { PageArticle } from "@/components/articles/PageArticle";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { chargerAxes, chargerMonArticle } from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/mon-club/actualites/$id")({
  gcTime: 0,
  beforeLoad: ({ context }) => {
    if (context.moi.role !== "eleve") throw redirect({ to: "/mon-club" });
  },
  loader: async ({ params }) => {
    const [article, axes] = await Promise.all([
      chargerMonArticle(params.id, "actualite"),
      chargerAxes(),
    ]);
    return { article, axes };
  },
  head: () => ({
    meta: [
      { title: "Actualité du club — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: Actualite,
});

function Actualite() {
  const { article, axes } = Route.useLoaderData();
  return (
    <PageArticle titre="Actualité" accent="du club" retour="club">
      <Editeur key={article.id} article={article} axes={axes} eleve nature="actualite" />
    </PageArticle>
  );
}
