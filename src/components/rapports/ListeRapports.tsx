import { Link } from "@tanstack/react-router";
import { Eye, EyeOff, FileText } from "lucide-react";

import { EtatRapport } from "@/components/rapports/EtatRapport";
import type { RapportResume } from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";
import { MODELES } from "@/lib/rapports";

// Une liste de rapports (spec 038) : état, référence, période, points ; pour le club, qui l'a reçu et qui l'a
// consulté.
export function ListeRapports({ rapports, vide }: { rapports: RapportResume[]; vide: string }) {
  if (rapports.length === 0) {
    return (
      <div className="rounded-3xl bg-card p-8 text-center shadow-card">
        <FileText className="mx-auto size-10 text-logo-blue/40" />
        <p className="mt-3 font-semibold">{vide}</p>
      </div>
    );
  }
  return (
    <ul className="space-y-3">
      {rapports.map((r) => (
        <li key={r.id}>
          <Link
            to="/rapports/$id"
            params={{ id: r.id }}
            className="block rounded-3xl bg-card p-5 shadow-card transition hover:-translate-y-0.5"
          >
            <p className="text-xs font-extrabold uppercase tracking-wider text-logo-blue">
              {MODELES[r.modele].libelle}
              {r.reference && ` · ${r.reference}`}
            </p>
            <p className="mt-1 break-words font-display text-xl text-ink">{r.titre}</p>
            <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
              <EtatRapport etat={r.etat} />
              {r.periode && <span>{r.periode}</span>}
              {!r.mien && <span>par {r.auteur}</span>}
              <span>Modifié le {dateCourte(r.modifie_le)}</span>
              {r.points !== null && <span className="font-bold text-ink">+{r.points} points</span>}
              {r.doublon_de && <span>Lié à {r.doublon_de}</span>}
            </div>
            {r.lectures.length > 0 && (
              <ul className="mt-2 flex flex-wrap gap-2 text-xs font-semibold">
                {r.lectures.map((l) => (
                  <li
                    key={l.nom}
                    className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 ${l.consulte_le ? "bg-leaf/20 text-ink" : "bg-mist text-muted-foreground"}`}
                  >
                    {l.consulte_le ? (
                      <Eye className="size-3" aria-hidden />
                    ) : (
                      <EyeOff className="size-3" aria-hidden />
                    )}
                    {l.nom} : {l.consulte_le ? `consulté le ${dateCourte(l.consulte_le)}` : "reçu"}
                  </li>
                ))}
              </ul>
            )}
          </Link>
        </li>
      ))}
    </ul>
  );
}
