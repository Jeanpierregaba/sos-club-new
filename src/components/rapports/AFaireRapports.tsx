import { Link } from "@tanstack/react-router";
import { ClipboardList } from "lucide-react";

import type { RapportResume } from "@/lib/api/client";
import { MODELES } from "@/lib/rapports";

// « À faire » (spec 038) : les brouillons à finir et les rapports que l'équipe demande de corriger.
export function AFaireRapports({ rapports }: { rapports: RapportResume[] }) {
  const aFaire = rapports.filter((r) => r.etat === "brouillon" || r.etat === "a_corriger");
  if (aFaire.length === 0) return null;
  return (
    <section className="mt-6 rounded-3xl bg-sun/25 p-5 ring-1 ring-sun">
      <h2 className="flex items-center gap-2 font-display text-xl text-ink">
        <ClipboardList className="size-5 text-logo-blue" /> À faire
      </h2>
      <ul className="mt-3 space-y-2">
        {aFaire.slice(0, 5).map((r) => (
          <li key={r.id}>
            <Link
              to="/rapports/$id"
              params={{ id: r.id }}
              className="font-bold text-logo-blue underline-offset-4 hover:underline"
            >
              {r.etat === "a_corriger" ? "Corriger" : "Finir"} : {MODELES[r.modele].libelle} «{" "}
              {r.titre} »
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
