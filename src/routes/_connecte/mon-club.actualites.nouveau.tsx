import { createFileRoute, redirect } from "@tanstack/react-router";

import { Editeur } from "@/components/articles/Editeur";
import { PageArticle } from "@/components/articles/PageArticle";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { chargerAxes } from "@/lib/api/client";

// Une actualité au nom du club (spec 026) : l'éditeur des articles, pour le président.
export const Route = createFileRoute("/_connecte/mon-club/actualites/nouveau")({
  gcTime: 0,
  beforeLoad: ({ context }) => {
    if (context.moi.role !== "eleve") throw redirect({ to: "/mon-club" });
  },
  loader: async () => ({ axes: await chargerAxes() }),
  head: () => ({
    meta: [
      { title: "Écrire une actualité — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: Nouvelle,
});

function Nouvelle() {
  const { axes } = Route.useLoaderData();
  return (
    <PageArticle titre="Nouvelle" accent="actualité" retour="club">
      <Editeur article={null} axes={axes} eleve nature="actualite" />
    </PageArticle>
  );
}
