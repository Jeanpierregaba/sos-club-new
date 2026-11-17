import { useState } from "react";

import { ErreurApi, repondreEvenement } from "@/lib/api/client";
import type { EvenementPublic, ReponseAgenda } from "@/lib/api/client";
import { REPONSES } from "@/lib/agenda";

const ORDRE: ReponseAgenda[] = ["participe", "peut_etre", "non"];

// La réponse d'un membre invité : trois choix, modifiables jusqu'au début de l'événement. Le serveur tranche
// (membre du club, places, début) ; le message de son refus s'affiche tel quel.
export function ChoixReponse({
  evenement,
  onReponse,
}: {
  evenement: EvenementPublic;
  onReponse?: (evenement: EvenementPublic) => void;
}) {
  const [actuelle, setActuelle] = useState<ReponseAgenda | null>(evenement.ma_reponse ?? null);
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);

  async function choisir(reponse: ReponseAgenda) {
    setEnCours(true);
    setErreur(null);
    try {
      const vue = await repondreEvenement(evenement.id, reponse);
      setActuelle(vue.ma_reponse ?? null);
      onReponse?.(vue);
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : "Ta réponse n'a pas pu être enregistrée.");
    } finally {
      setEnCours(false);
    }
  }

  return (
    <div className="rounded-[1.5rem] bg-mist-soft p-4">
      <p className="text-sm font-extrabold">Ton club t'invite. Tu viens ?</p>
      <div role="group" aria-label="Ta réponse" className="mt-3 flex flex-wrap gap-2">
        {ORDRE.map((reponse) => {
          const choisie = actuelle === reponse;
          const complet = reponse === "participe" && evenement.complet && !choisie;
          return (
            <button
              key={reponse}
              type="button"
              aria-pressed={choisie}
              disabled={enCours || complet}
              onClick={() => void choisir(reponse)}
              className={`h-11 rounded-full px-5 text-sm font-bold transition disabled:opacity-50 ${
                choisie
                  ? "bg-primary text-primary-foreground"
                  : "bg-white ring-1 ring-border hover:ring-primary"
              }`}
            >
              {REPONSES[reponse]}
            </button>
          );
        })}
      </div>
      {evenement.complet && actuelle !== "participe" && (
        <p className="mt-2 text-sm font-semibold text-muted-foreground">
          L'événement est complet : tu peux répondre « Peut-être ».
        </p>
      )}
      {erreur && (
        <p role="alert" className="mt-2 text-sm font-semibold text-logo-red">
          {erreur}
        </p>
      )}
    </div>
  );
}
