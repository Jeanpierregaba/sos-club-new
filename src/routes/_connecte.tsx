import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";

import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { chargerMoi } from "@/lib/api/client";

// Cette garde ne sert qu'à l'affichage : c'est l'API qui protège les données.
export const Route = createFileRoute("/_connecte")({
  beforeLoad: async ({ location }) => {
    const moi = await chargerMoi();
    if (!moi) throw redirect({ to: "/connexion", search: { redirection: location.href } });
    return { moi };
  },
  gcTime: 0,
  // Sur un téléphone partagé, le bouton retour ne doit pas réafficher une page de compte.
  headers: () => ({ "Cache-Control": "no-store" }),
  errorComponent: ServiceIndisponible,
  component: Outlet,
});
