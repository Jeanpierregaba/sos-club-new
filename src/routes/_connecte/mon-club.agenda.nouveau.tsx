import { createFileRoute, useNavigate } from "@tanstack/react-router";

import { FormulaireEvenement } from "@/components/agenda/FormulaireEvenement";
import { PageArticle } from "@/components/articles/PageArticle";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { chargerAxes, creerEvenement } from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/mon-club/agenda/nouveau")({
  gcTime: 0,
  loader: async () => ({ axes: await chargerAxes() }),
  head: () => ({
    meta: [
      { title: "Proposer un événement — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: Nouvel,
});

function Nouvel() {
  const { axes } = Route.useLoaderData();
  const naviguer = useNavigate();
  return (
    <PageArticle titre="Proposer" accent="un événement" retour="club">
      <p className="-mt-2 mb-6 font-medium text-muted-foreground">
        Enregistre ton brouillon, relis-le, puis soumets-le à l'équipe nationale depuis sa page.
      </p>
      <FormulaireEvenement
        axes={axes}
        bouton="Enregistrer le brouillon"
        onEnvoi={async (champs) => {
          const evenement = await creerEvenement(champs);
          await naviguer({ to: "/mon-club/agenda/$id", params: { id: evenement.id } });
        }}
      />
    </PageArticle>
  );
}
