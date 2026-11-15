import { Link } from "@tanstack/react-router";
import { AlertTriangle, Award, Snowflake, Undo2, UserX } from "lucide-react";

import { REGLE_EX_AEQUO } from "@/components/classements/Palmares";
import { Button } from "@/components/ui/button";
import type { CandidatAdmin, ClotureDetail } from "@/lib/api/client";
import { formaterPoints } from "@/lib/classements";
import { dateHeure } from "@/lib/dates";

export type ActionCloture = "gel" | "validation" | "publication" | "annulation";

// Les actions possibles sur une clôture selon son état (spec 037) : geler un semestre terminé, regeler ou valider
// une clôture gelée, publier ou annuler une validation. Rien après la publication. L'API revérifie tout.
export function ActionsCloture({
  etat,
  termine,
  onAction,
}: {
  etat: "ouvert" | ClotureDetail["etat"];
  termine: boolean;
  onAction: (action: ActionCloture) => void;
}) {
  if (etat === "publie" || (etat === "ouvert" && !termine)) return null;
  return (
    <div className="flex flex-wrap gap-2 rounded-3xl bg-white p-4 ring-1 ring-border">
      {((etat === "ouvert" && termine) || etat === "gele") && (
        <Button
          onClick={() => onAction("gel")}
          variant={etat === "ouvert" ? "default" : "outline"}
          className="rounded-full font-bold"
        >
          <Snowflake className="size-4" /> {etat === "ouvert" ? "Geler le classement" : "Regeler"}
        </Button>
      )}
      {etat === "gele" && (
        <Button onClick={() => onAction("validation")} className="btn-fx rounded-full font-bold">
          <Award className="size-4" /> Valider le Top 3
        </Button>
      )}
      {etat === "valide" && (
        <>
          <Button onClick={() => onAction("publication")} className="btn-fx rounded-full font-bold">
            <Award className="size-4" /> Publier le palmarès
          </Button>
          <Button
            variant="outline"
            onClick={() => onAction("annulation")}
            className="rounded-full font-bold"
          >
            <Undo2 className="size-4" /> Annuler la validation
          </Button>
        </>
      )}
    </div>
  );
}

// La photo d'une clôture : Top 3, écart avec le classement actuel et candidats avec leurs contrôles.
export function DetailCloture({
  cloture,
  modificateur,
  onEcarter,
  onReintegrer,
}: {
  cloture: ClotureDetail;
  modificateur: boolean;
  onEcarter: (candidat: CandidatAdmin) => void;
  onReintegrer: (candidat: CandidatAdmin) => void;
}) {
  const controle = modificateur && cloture.etat === "gele";
  const ecart = cloture.ecart_actuel;
  return (
    <>
      <div className="space-y-3 rounded-3xl bg-white p-5 ring-1 ring-border">
        <h3 className="font-display text-xl text-logo-blue">
          {cloture.etat === "gele" ? "Top 3 proposé" : "Top 3"}
        </h3>
        {cloture.top3.length === 0 ? (
          <p className="font-semibold text-muted-foreground">Aucun candidat retenu.</p>
        ) : (
          <ol className="grid gap-3 sm:grid-cols-3">
            {cloture.top3.map((laureat, index) => (
              <li key={laureat.utilisateur_id} className="rounded-2xl bg-mist-soft p-4">
                <p className="text-xs font-extrabold uppercase tracking-wider text-logo-blue">
                  {laureat.distinction}
                </p>
                <p className="mt-1 break-words font-bold text-ink">{laureat.pseudonyme}</p>
                <p className="text-xs font-semibold text-muted-foreground">
                  {[laureat.club, laureat.dre].filter(Boolean).join(" · ")} ·{" "}
                  {formaterPoints(laureat.points)} pts
                </p>
                <span className="sr-only">Place {index + 1}</span>
              </li>
            ))}
          </ol>
        )}
        <p className="text-xs font-medium text-muted-foreground">{REGLE_EX_AEQUO}</p>
      </div>

      {(ecart.top3_different || ecart.changements.length > 0) && (
        <div
          role="status"
          className="flex gap-3 rounded-3xl bg-sun/25 p-4 text-sm font-semibold text-ink ring-1 ring-sun"
        >
          <AlertTriangle aria-hidden className="size-5 shrink-0 text-logo-red" />
          <div>
            <p className="font-bold">
              Le classement actuel diffère de la photo
              {ecart.top3_different ? " et le Top 3 changerait" : ""}.
            </p>
            <ul className="mt-1 list-disc pl-5">
              {ecart.changements.map((c) => (
                <li key={c.pseudonyme}>
                  {c.pseudonyme} : {c.points_gel ?? "absent"} →{" "}
                  {c.points_actuels === null
                    ? "plus classable (suspendu, ancien ou total nul)"
                    : `${c.points_actuels}${c.hors_photo ? " (au-delà des 50 premiers)" : ""}`}
                </li>
              ))}
            </ul>
            {cloture.etat === "gele" && <p className="mt-1">Regèle pour en tenir compte.</p>}
          </div>
        </div>
      )}

      <div className="overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-border">
        <p className="border-b px-5 py-3 text-sm font-bold text-ink">
          Photo du {dateHeure(cloture.etapes.gele_le)} par {cloture.etapes.gele_par} ·{" "}
          {cloture.candidats.length} candidat{cloture.candidats.length > 1 ? "s" : ""}
          {cloture.etapes.valide_le &&
            ` · validé le ${dateHeure(cloture.etapes.valide_le)} par ${cloture.etapes.valide_par}`}
          {cloture.etapes.publie_le &&
            ` · publié le ${dateHeure(cloture.etapes.publie_le)} par ${cloture.etapes.publie_par}`}
        </p>
        {cloture.candidats.length === 0 ? (
          <p className="p-6 text-center font-semibold text-muted-foreground">
            Aucun élève classé ce semestre.
          </p>
        ) : (
          <ol className="divide-y">
            {cloture.candidats.map((c) => (
              <li
                key={c.utilisateur_id}
                className={`flex flex-wrap items-start gap-3 px-4 py-3 sm:px-5 ${c.ecarte ? "bg-logo-red/5" : ""}`}
              >
                <span className="w-14 shrink-0 text-center font-display text-lg text-logo-blue">
                  {c.rang}
                  {c.rang_brut !== c.rang && (
                    <span className="block text-[11px] font-semibold text-muted-foreground">
                      ex æquo {c.rang_brut}
                    </span>
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="break-words font-bold text-ink">
                    {c.pseudonyme}{" "}
                    <span className="text-xs font-semibold text-muted-foreground">
                      ({c.identifiant}) · {c.statut}
                    </span>
                  </p>
                  <p className="break-words text-xs font-semibold text-muted-foreground">
                    {[c.club, c.dre].filter(Boolean).join(" · ")} · total atteint le{" "}
                    {dateHeure(c.atteint_le)} · {c.corrections} correction
                    {c.corrections > 1 ? "s" : ""}, {c.annulations} annulation
                    {c.annulations > 1 ? "s" : ""} ·{" "}
                    <Link
                      to="/admin/points/registre"
                      search={{ recherche: c.identifiant, semestre_id: cloture.semestre.id }}
                      className="font-bold text-logo-blue underline-offset-2 hover:underline"
                    >
                      Voir au registre
                    </Link>
                  </p>
                  {c.motif_ecart && (
                    <p className="mt-1 break-words text-sm italic text-logo-red">
                      Écarté
                      {c.ecarte_le ? ` le ${dateHeure(c.ecarte_le)}` : ""}
                      {c.ecarte_par ? ` par ${c.ecarte_par}` : ""} : « {c.motif_ecart} »
                    </p>
                  )}
                </div>
                <span className="shrink-0 font-extrabold text-ink">
                  {formaterPoints(c.points)} pts
                </span>
                {controle &&
                  (c.ecarte ? (
                    <Button
                      variant="outline"
                      size="sm"
                      className="rounded-full"
                      onClick={() => onReintegrer(c)}
                      aria-label={`Réintégrer ${c.pseudonyme}`}
                    >
                      <Undo2 className="size-4" /> Réintégrer
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      className="rounded-full"
                      onClick={() => onEcarter(c)}
                      aria-label={`Écarter ${c.pseudonyme}`}
                    >
                      <UserX className="size-4" /> Écarter
                    </Button>
                  ))}
              </li>
            ))}
          </ol>
        )}
      </div>
    </>
  );
}
