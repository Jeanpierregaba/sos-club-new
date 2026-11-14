import { createFileRoute, Link, Outlet, redirect } from "@tanstack/react-router";

import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { peut } from "@/lib/admin";

export const Route = createFileRoute("/_connecte/admin/points")({
  beforeLoad: ({ context }) => {
    if (!peut(context.admin, "points", "consulter")) throw redirect({ to: "/admin" });
  },
  component: Points,
});

const ONGLETS = [
  { to: "/admin/points", libelle: "Semestres", exact: true },
  { to: "/admin/points/bareme", libelle: "Barème", exact: false },
  { to: "/admin/points/annees", libelle: "Années académiques", exact: false },
  { to: "/admin/points/gold", libelle: "Élèves Gold", exact: false },
] as const;

function Points() {
  return (
    <div className="space-y-6">
      <EnTeteAdmin sur="Points et classements" bleu="Semestres et" vert="barème">
        Chaque point est une ligne du registre, avec son semestre. Un changement vaut pour les gains
        à venir : les points déjà gagnés ne bougent pas.
      </EnTeteAdmin>
      <nav aria-label="Parties des points" className="flex flex-wrap gap-2">
        {ONGLETS.map((o) => (
          <Link
            key={o.to}
            to={o.to}
            activeOptions={{ exact: o.exact, includeSearch: false }}
            className="rounded-full bg-white px-4 py-2 text-sm font-bold ring-1 ring-border transition hover:ring-night/30"
            activeProps={{ className: "!bg-night text-white !ring-night" }}
          >
            {o.libelle}
          </Link>
        ))}
      </nav>
      <Outlet />
    </div>
  );
}
