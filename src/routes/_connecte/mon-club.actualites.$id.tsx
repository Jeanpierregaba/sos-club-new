import { createFileRoute, redirect } from "@tanstack/react-router";

import { Editeur } from "@/components/articles/Editeur";
import { PageArticle } from "@/components/articles/PageArticle";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { chargerAxes, chargerMonArticle, chargerMonClub, ErreurApi } from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/mon-club/actualites/$id")({
  gcTime: 0,
  // Le président en place seulement : un membre, un encadreur ou un ancien président revient à « Mon club ».
  beforeLoad: async ({ context }) => {
    const { club } = await chargerMonClub().catch(() => ({ club: null }));
    if (context.moi.role !== "eleve" || !club?.president || club.etat !== "actif")
      throw redirect({ to: "/mon-club" });
  },
  loader: async ({ params }) => {
    try {
      const [article, axes] = await Promise.all([
        chargerMonArticle(params.id, "actualite"),
        chargerAxes(),
      ]);
      return { article, axes };
    } catch (e) {
      // Une actualité d'un autre club, ou supprimée : retour à « Mon club » plutôt qu'une panne.
      if (e instanceof ErreurApi && (e.statut === 403 || e.statut === 404))
        throw redirect({ to: "/mon-club" });
      throw e;
    }
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
