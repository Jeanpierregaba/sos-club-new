import { createFileRoute, redirect } from "@tanstack/react-router";

import { Editeur } from "@/components/articles/Editeur";
import { PageArticle } from "@/components/articles/PageArticle";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { chargerAxes } from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/mes-articles/nouveau")({
  gcTime: 0,
  beforeLoad: ({ context }) => {
    if (context.moi.role === "admin") throw redirect({ to: "/admin" });
  },
  loader: async () => ({ axes: await chargerAxes() }),
  head: () => ({
    meta: [
      { title: "Écrire un article — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: Nouveau,
});

function Nouveau() {
  const { axes } = Route.useLoaderData();
  const { moi } = Route.useRouteContext();
  return (
    <PageArticle titre="Nouvel" accent="article">
      <Editeur article={null} axes={axes} eleve={moi.role === "eleve"} />
    </PageArticle>
  );
}
