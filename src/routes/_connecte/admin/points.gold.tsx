import { createFileRoute } from "@tanstack/react-router";
import { Crown } from "lucide-react";

import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { adminListerGold } from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/admin/points/gold")({
  loader: () => adminListerGold(),
  gcTime: 0,
  errorComponent: ServiceIndisponible,
  component: Gold,
});

// Les élèves à la carte Gold (spec 034) : éligibles au tirage au sort des fournitures scolaires, dont le règlement
// reste à écrire. Pseudonyme, club et DRE seulement.
function Gold() {
  const eleves = Route.useLoaderData();
  return (
    <section className="space-y-4">
      <p className="max-w-3xl text-sm font-medium text-muted-foreground">
        Un élève passe Gold quand il a les 4 étoiles des Jeux, c'est-à-dire tous les quiz de chaque
        niveau réussis. Le tirage au sort suivra son règlement.
      </p>
      {eleves.length === 0 ? (
        <p className="rounded-3xl border border-dashed p-8 text-center font-semibold text-muted-foreground">
          Aucun élève n'a encore la carte Gold.
        </p>
      ) : (
        <ul className="divide-y overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-border">
          {eleves.map((e) => (
            <li key={e.utilisateur_id} className="flex flex-wrap items-center gap-3 px-5 py-4">
              <Crown aria-hidden className="size-5 text-sun" />
              <div className="min-w-0 flex-1">
                <p className="font-bold text-ink">{e.pseudonyme}</p>
                <p className="text-xs font-semibold text-muted-foreground">
                  {e.club ?? "Non affilié"} · {e.etablissement} · {e.dre}
                </p>
              </div>
              <span className="text-xs font-bold text-muted-foreground">
                Gold depuis le {new Date(e.gold_le).toLocaleDateString("fr-FR")}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
