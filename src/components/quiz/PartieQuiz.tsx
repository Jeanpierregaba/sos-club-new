import { Loader2, PartyPopper, RotateCcw, Timer } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  type AppelsPartie,
  type EtatPartie,
} from "@/lib/api/client";

// Délai avant de redemander l'état quand le temps affiché est écoulé : le serveur accorde une tolérance réseau,
// et c'est lui seul qui déclare la question ratée.
const ATTENTE_APRES_TEMPS_MS = 1000;

const LETTRES = ["A", "B", "C", "D"];

// Une partie de quiz (spec 027). Le site affiche la question et un compte à rebours ; il ne décide jamais du
// résultat : chaque réponse part au serveur, qui renvoie la question suivante ou le score final.
export function PartieQuiz({
  depart,
  appels,
  avecPoints,
  onRejouer,
  actions,
}: {
  depart: EtatPartie;
  appels: AppelsPartie;
  // Un élève gagne des points ; un encadreur ou un essai de l'équipe, non : le résultat n'en parle pas.
  avecPoints: boolean;
  onRejouer?: () => Promise<void> | void;
  actions?: ReactNode;
}) {
  const [etat, setEtat] = useState(depart);
  const [restant, setRestant] = useState(depart.question?.restant_ms ?? 0);
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const occupe = useRef(false);

  useEffect(() => setEtat(depart), [depart]);

  const question = etat.question;
  const cle = question ? `${etat.tentative_id}:${question.rang}` : null;

  const appeler = useCallback(async (action: () => Promise<EtatPartie>) => {
    if (occupe.current) return;
    occupe.current = true;
    setEnCours(true);
    setErreur(null);
    try {
      setEtat(await action());
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      occupe.current = false;
      setEnCours(false);
    }
  }, []);

  // Le compte à rebours de la question en cours, recalé à chaque état reçu du serveur : une nouvelle question,
  // ou la même renvoyée (temps écoulé, tolérance en cours), qui relance la demande un peu plus tard.
  useEffect(() => {
    const enCoursDeJeu = etat.question;
    if (!enCoursDeJeu) return;
    const fin = Date.now() + enCoursDeJeu.restant_ms;
    setRestant(enCoursDeJeu.restant_ms);
    let relance: ReturnType<typeof setTimeout> | undefined;
    const minuterie = setInterval(() => {
      const reste = Math.max(0, fin - Date.now());
      setRestant(reste);
      if (reste === 0) {
        clearInterval(minuterie);
        relance = setTimeout(
          () => void appeler(() => appels.reprendre(etat.tentative_id)),
          ATTENTE_APRES_TEMPS_MS,
        );
      }
    }, 100);
    return () => {
      clearInterval(minuterie);
      if (relance) clearTimeout(relance);
    };
  }, [etat, appels, appeler]);

  if (!question && etat.resultat) {
    const r = etat.resultat;
    return (
      <div className="space-y-5 text-center">
        {r.reussie ? (
          <PartyPopper aria-hidden className="mx-auto size-12 text-primary" />
        ) : (
          <RotateCcw aria-hidden className="mx-auto size-12 text-logo-blue" />
        )}
        <p className="font-display text-6xl text-ink">
          {r.score}
          <span className="text-3xl text-muted-foreground"> / {r.total}</span>
        </p>
        <p role="status" className="text-lg font-bold text-ink">
          {r.reussie
            ? "Bravo, quiz réussi !"
            : `Pas encore : il faut ${r.seuil} bonnes réponses pour réussir.`}
        </p>
        {avecPoints && r.points > 0 && (
          <p className="inline-flex rounded-full bg-primary/15 px-4 py-2 font-bold text-primary">
            +{r.points} points
          </p>
        )}
        {avecPoints && r.reussie && r.points === 0 && (
          <p className="text-sm text-muted-foreground">
            Tu as déjà gagné les points de ce quiz : rejouer sert à t'entraîner.
          </p>
        )}
        <div className="flex flex-wrap justify-center gap-3">
          {onRejouer && (
            <Button
              className="h-11 rounded-full px-6 font-bold"
              disabled={enCours}
              onClick={() => void onRejouer()}
            >
              <RotateCcw className="size-4" /> Rejouer
            </Button>
          )}
          {actions}
        </div>
      </div>
    );
  }

  if (!question) return null;
  const part = question.temps_ms > 0 ? restant / question.temps_ms : 0;
  const secondes = Math.ceil(restant / 1000);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between text-sm font-bold text-muted-foreground">
        <span>
          Question {question.rang} / {etat.total}
        </span>
        <span className="inline-flex items-center gap-1" aria-label={`${secondes} secondes`}>
          <Timer aria-hidden className="size-4" /> {secondes} s
        </span>
      </div>
      <div
        aria-hidden
        className="h-2 overflow-hidden rounded-full bg-muted"
        data-testid="barre-temps"
      >
        <div
          className={`h-full rounded-full transition-[width] duration-100 ${part > 0.4 ? "bg-primary" : "bg-logo-red"}`}
          style={{ width: `${Math.round(part * 100)}%` }}
        />
      </div>
      <h2 className="font-display text-2xl leading-snug text-ink">{question.enonce}</h2>
      <div className="grid gap-3">
        {question.choix.map((texte, i) => (
          <button
            key={`${cle}:${i}`}
            type="button"
            disabled={enCours || restant === 0}
            onClick={() => void appeler(() => appels.repondre(etat.tentative_id, question.rang, i))}
            className="flex min-h-14 items-center gap-3 rounded-2xl bg-white px-4 py-3 text-left font-semibold text-ink shadow-sm ring-1 ring-border transition hover:ring-primary disabled:opacity-60"
          >
            <span className="grid size-8 shrink-0 place-items-center rounded-full bg-mist font-bold text-logo-blue">
              {LETTRES[i]}
            </span>
            {texte}
          </button>
        ))}
      </div>
      {restant === 0 && (
        <p className="flex items-center gap-2 text-sm font-semibold text-logo-red">
          <Loader2 className="size-4 animate-spin" /> Temps écoulé…
        </p>
      )}
      {erreur && (
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center gap-3">
            {erreur}
            <Button
              size="sm"
              variant="outline"
              className="rounded-full"
              onClick={() => void appeler(() => appels.reprendre(etat.tentative_id))}
            >
              Reprendre
            </Button>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
