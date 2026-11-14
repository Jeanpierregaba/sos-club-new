import { createFileRoute, Link, Outlet, redirect } from "@tanstack/react-router";

import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { peut } from "@/lib/admin";

// La certification Génie Imhotep (spec 029) : ses quiz se préparent dans la banque, le reste se gère ici avec les
// droits `quiz`.
export const Route = createFileRoute("/_connecte/admin/certification")({
  beforeLoad: ({ context }) => {
    if (!peut(context.admin, "quiz", "consulter")) throw redirect({ to: "/admin" });
  },
  component: Certification,
});

const ONGLETS = [
  { to: "/admin/certification", libelle: "Certificats", exact: true },
  { to: "/admin/certification/badges", libelle: "Badges", exact: false },
  { to: "/admin/certification/parametres", libelle: "Paramètres du parcours", exact: false },
] as const;

function Certification() {
  return (
    <div className="space-y-6">
      <EnTeteAdmin sur="Quiz et certification" bleu="Certification" vert="Génie Imhotep">
        Les 20 quiz du parcours se préparent dans la{" "}
        <Link
          to="/admin/quiz"
          search={{ parcours: "certification" }}
          className="font-bold text-logo-blue underline"
        >
          banque de quiz
        </Link>
        . Ici : les certificats délivrés, les règles des badges et les paramètres des parties.
      </EnTeteAdmin>
      <nav aria-label="Parties de la certification" className="flex flex-wrap gap-2">
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
