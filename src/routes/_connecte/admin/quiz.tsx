import { createFileRoute, Link, Outlet, redirect } from "@tanstack/react-router";

import { EnTeteAdmin } from "@/components/admin/EnTeteAdmin";
import { peut } from "@/lib/admin";

export const Route = createFileRoute("/_connecte/admin/quiz")({
  beforeLoad: ({ context }) => {
    if (!peut(context.admin, "quiz", "consulter")) throw redirect({ to: "/admin" });
  },
  component: Quiz,
});

const ONGLETS = [
  { to: "/admin/quiz", libelle: "Banque de quiz", exact: true },
  { to: "/admin/quiz/parametres", libelle: "Paramètres", exact: false },
] as const;

function Quiz() {
  return (
    <div className="space-y-6">
      <EnTeteAdmin sur="Quiz et certification" bleu="Banque de" vert="quiz">
        Le gestionnaire pédagogique prépare et soumet ; un autre membre de l'équipe publie, en
        nommant la personne qui a validé le contenu médical.
      </EnTeteAdmin>
      <nav aria-label="Parties des quiz" className="flex flex-wrap gap-2">
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
