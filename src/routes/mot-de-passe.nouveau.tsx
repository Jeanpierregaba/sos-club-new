import { createFileRoute, useNavigate } from "@tanstack/react-router";

import { NouveauMotDePasse } from "@/components/comptes/NouveauMotDePasse";
import { verifierLienMotDePasse } from "@/lib/api/client";
import { m } from "@/paraglide/messages.js";

export const Route = createFileRoute("/mot-de-passe/nouveau")({
  validateSearch: (search: Record<string, unknown>): { jeton?: string } =>
    typeof search["jeton"] === "string" && /^[A-Za-z0-9_-]{20,100}$/.test(search["jeton"])
      ? { jeton: search["jeton"] }
      : {},
  loaderDeps: ({ search }) => ({ jeton: search.jeton }),
  // Une API en panne affiche le message du lien invalide plutôt qu'une page d'erreur : on peut redemander un lien.
  loader: async ({ deps }) =>
    deps.jeton
      ? await verifierLienMotDePasse(deps.jeton)
          .then((r) => r.valide)
          .catch(() => false)
      : false,
  head: () => ({
    meta: [
      { title: m.mdp_nouveau_meta() },
      { name: "robots", content: "noindex" },
      // Le jeton est dans l'adresse : aucune page suivante ne doit le recevoir.
      { name: "referrer", content: "no-referrer" },
    ],
  }),
  component: PageNouveauMotDePasse,
});

function PageNouveauMotDePasse() {
  const valide = Route.useLoaderData();
  const { jeton } = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  return (
    <NouveauMotDePasse
      jeton={jeton}
      valide={valide}
      // Le jeton ne reste pas dans l'historique du navigateur.
      onFait={() => navigate({ search: {}, replace: true })}
    />
  );
}
