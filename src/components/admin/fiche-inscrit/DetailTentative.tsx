import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { dateHeure, dureeLisible } from "@/lib/admin";
import { chargerTentativeInscrit, type QuestionTentative } from "@/lib/api/client";

import { Chargement, Pastille } from "./commun";
import { useChargement } from "./useChargement";

const ETATS: Record<
  QuestionTentative["etat"],
  { libelle: string; ton: "vert" | "rouge" | "gris" | "or" }
> = {
  juste: { libelle: "Juste", ton: "vert" },
  fausse: { libelle: "Fausse", ton: "rouge" },
  temps_ecoule: { libelle: "Temps écoulé", ton: "or" },
  non_posee: { libelle: "Non posée", ton: "gris" },
  en_cours: { libelle: "En cours", ton: "gris" },
};

// Spec 046 : les questions d'une tentative, le temps mis sur chacune. Jamais la bonne réponse.
export function DetailTentative({
  id,
  tentativeId,
  fermer,
}: {
  id: string;
  tentativeId: string;
  fermer: () => void;
}) {
  const { donnees, erreur } = useChargement(
    () => chargerTentativeInscrit(id, tentativeId),
    [id, tentativeId],
  );

  return (
    <Dialog open onOpenChange={(ouvert) => !ouvert && fermer()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{donnees ? donnees.tentative.quiz_titre : "Tentative"}</DialogTitle>
          <DialogDescription>
            {donnees
              ? `${dateHeure(donnees.tentative.commencee_le)} · temps de jeu ${dureeLisible(donnees.tentative.duree_s)} · ${donnees.temps_imparti_s} s par question`
              : "Questions de la tentative et temps mis sur chacune."}
          </DialogDescription>
        </DialogHeader>
        {!donnees ? (
          <Chargement erreur={erreur} />
        ) : donnees.questions.length === 0 ? (
          <p className="text-sm font-medium text-muted-foreground">
            Aucune question enregistrée pour cette tentative.
          </p>
        ) : (
          <>
            <ol className="divide-y text-sm">
              {donnees.questions.map((q) => {
                const etat = ETATS[q.etat];
                return (
                  <li key={q.rang} className="flex items-start justify-between gap-4 py-3">
                    <span className="min-w-0">
                      <span className="block font-bold">
                        {q.rang}. {q.enonce}
                      </span>
                      <span className="mt-1 flex flex-wrap items-center gap-2 text-muted-foreground">
                        <Pastille ton={etat.ton}>{etat.libelle}</Pastille>
                        {q.reponse && <span>Réponse : {q.reponse}</span>}
                      </span>
                    </span>
                    <span className="shrink-0 font-extrabold tabular-nums">
                      {dureeLisible(q.secondes)}
                    </span>
                  </li>
                );
              })}
            </ol>
            <p className="text-xs font-medium text-muted-foreground">
              Le temps d'une question va de son affichage à la réponse. Le temps de jeu de la
              tentative compte aussi la lecture des corrections entre deux questions.
            </p>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
