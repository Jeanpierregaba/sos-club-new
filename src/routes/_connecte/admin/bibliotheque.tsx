import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";

import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { peut } from "@/lib/admin";

export const Route = createFileRoute("/_connecte/admin/bibliotheque")({
  beforeLoad: ({ context }) => {
    if (!peut(context.admin, "bibliotheque", "consulter")) throw redirect({ to: "/admin" });
  },
  component: Bibliotheque,
});

function Bibliotheque() {
  return (
    <div className="space-y-6">
      <EnTeteAdmin sur="Bibliothèque" bleu="Ressources" vert="en PDF">
        Un membre de l'équipe prépare et soumet ; un autre publie, en nommant la personne qui a
        validé le contenu.
      </EnTeteAdmin>
      <Outlet />
    </div>
  );
}
