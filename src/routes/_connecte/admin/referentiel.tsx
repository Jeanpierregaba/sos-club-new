import { createFileRoute, Link, Outlet, redirect } from "@tanstack/react-router";

import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { peut } from "@/lib/admin";

export const Route = createFileRoute("/_connecte/admin/referentiel")({
  beforeLoad: ({ context }) => {
    if (!peut(context.admin, "clubs", "consulter")) throw redirect({ to: "/admin" });
  },
  component: Referentiel,
});

const ONGLETS = [
  { to: "/admin/referentiel", libelle: "DRE et IESG", exact: true },
  { to: "/admin/referentiel/etablissements", libelle: "Établissements", exact: false },
  { to: "/admin/referentiel/axes", libelle: "Axes", exact: false },
] as const;

function Referentiel() {
  const { admin } = Route.useRouteContext();
  return (
    <div className="space-y-6">
      <EnTeteAdmin sur="Clubs et DRE" bleu="Le" vert="référentiel">
        Le découpage scolaire et les axes qui servent partout sur la plateforme. Rien ne se supprime
        : on renomme, on déplace ou on désactive.
        {!admin.super_admin && " Les DRE, IESG et axes se modifient par le super-administrateur."}
      </EnTeteAdmin>
      <nav aria-label="Parties du référentiel" className="flex flex-wrap gap-2">
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
