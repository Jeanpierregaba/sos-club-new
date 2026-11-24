import { QueryClient } from "@tanstack/react-query";
import { createRouter } from "@tanstack/react-router";
import { REECRITURE_LANGUES } from "./lib/langues";
import { routeTree } from "./routeTree.gen";

export const getRouter = () => {
  const queryClient = new QueryClient();
  // Spec 052 : `/en/<page non traduite>` renvoie vers la page française, `/en/<page inconnue>` est une 404.
  const pageExiste = (chemin: string): boolean => router.getMatchedRoutes(chemin)[2] !== undefined;

  const router = createRouter({
    routeTree,
    context: { queryClient, pageExiste },
    scrollRestoration: true,
    defaultPreloadStaleTime: 0,
    // Langues (spec 052).
    rewrite: REECRITURE_LANGUES,
  });

  return router;
};
