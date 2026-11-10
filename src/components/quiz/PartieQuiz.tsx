import { Check, Loader2, PartyPopper, RotateCcw, Timer, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  type AppelsPartie,
  type CorrectionReponse,
  type EtatPartie,
  type QuestionJoueur,
} from "@/lib/api/client";

// Délai avant de redemander l'état quand le temps affiché est écoulé : le serveur accorde une tolérance réseau,
// et c'est lui seul qui déclare la question ratée.
const ATTENTE_APRES_TEMPS_MS = 1000;

const LETTRES = ["A", "B", "C", "D"];

// Durée du retour vert ou rouge après une réponse (quiz des jeux, 2026-11-10). Le serveur ne démarre le chrono de la
// question suivante qu'après cette pause (PAUSE_CORRECTION dans backend/app/quiz/partie.py) : garder les deux égales.
export const DUREE_RETOUR_MS = 1200;

// La question corrigée reste affichée, puis l'état déjà reçu du serveur prend le relais.
type Retour = { question: QuestionJoueur; correction: CorrectionReponse; suivant: EtatPartie };

// Une partie de quiz (spec 027). Le site affiche la question et un compte à rebours ; il ne décide jamais du
// résultat : chaque réponse part au serveur, qui renvoie la question suivante ou le score final. Pour un quiz des
// jeux, le serveur corrige aussi la réponse donnée : le choix clignote en vert ou en rouge, puis la partie avance ;
// à la fin, un récapitulatif montre les questions ratées et leurs bonnes réponses.
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
  const [retour, setRetour] = useState<Retour | null>(null);
  const occupe = useRef(false);
  const titre = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    setRetour(null);
    setEtat(depart);
  }, [depart]);

  // Au bout de la pause, la partie avance ; un nouveau départ ou un démontage annule simplement le minuteur.
  useEffect(() => {
    if (!retour) return;
    const minuteur = setTimeout(() => {
      setRetour(null);
      setEtat(retour.suivant);
    }, DUREE_RETOUR_MS);
    return () => clearTimeout(minuteur);
  }, [retour]);

  const question = etat.question;

  // Chaque appel au serveur. Si sa réponse corrige la question affichée (réponse donnée, ou temps écoulé), le choix
  // clignote en vert ou en rouge pendant la pause, puis l'état reçu s'affiche.
  const appeler = useCallback(
    async (action: () => Promise<EtatPartie>, affichee?: QuestionJoueur | null) => {
      if (occupe.current) return;
      occupe.current = true;
      setEnCours(true);
      setErreur(null);
      try {
        const suivant = await action();
        const correction = suivant.correction;
        if (affichee && correction && correction.rang === affichee.rang) {
          setRetour({ question: affichee, correction, suivant });
        } else {
          setEtat(suivant);
        }
      } catch (e) {
        setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
      } finally {
        occupe.current = false;
        setEnCours(false);
      }
    },
    [],
  );

  const repondre = (question: QuestionJoueur, choix: number) =>
    appeler(() => appels.repondre(etat.tentative_id, question.rang, choix), question);

  // Le compte à rebours de la question en cours, recalé à chaque état reçu du serveur : une nouvelle question,
  // ou la même renvoyée (temps écoulé, tolérance en cours), qui relance la demande un peu plus tard.
  useEffect(() => {
    const enCoursDeJeu = etat.question;
    if (!enCoursDeJeu || retour) return;
    const fin = Date.now() + enCoursDeJeu.restant_ms;
    setRestant(enCoursDeJeu.restant_ms);
    let relance: ReturnType<typeof setTimeout> | undefined;
    const minuterie = setInterval(() => {
      const reste = Math.max(0, fin - Date.now());
      setRestant(reste);
      if (reste === 0) {
        clearInterval(minuterie);
        relance = setTimeout(
          () => void appeler(() => appels.reprendre(etat.tentative_id), enCoursDeJeu),
          ATTENTE_APRES_TEMPS_MS,
        );
      }
    }, 100);
    return () => {
      clearInterval(minuterie);
      if (relance) clearTimeout(relance);
    };
  }, [etat, appels, appeler, retour]);

  // Chaque nouvelle question prend le focus : le lecteur d'écran la lit, et le clavier repart du bon endroit.
  const rang = etat.question?.rang;
  useEffect(() => {
    if (rang !== undefined) titre.current?.focus();
  }, [etat.tentative_id, rang]);

  async function rejouer() {
    if (!onRejouer || occupe.current) return;
    occupe.current = true;
    setEnCours(true);
    setErreur(null);
    try {
      await onRejouer();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      occupe.current = false;
      setEnCours(false);
    }
  }

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
        {r.erreurs && <Recapitulatif erreurs={r.erreurs} />}
        <div className="flex flex-wrap justify-center gap-3">
          {onRejouer && (
            <Button
              className="h-11 rounded-full px-6 font-bold"
              disabled={enCours}
              onClick={() => void rejouer()}
            >
              <RotateCcw className="size-4" /> Rejouer
            </Button>
          )}
          {actions}
        </div>
        {erreur && (
          <Alert variant="destructive" className="text-left">
            <AlertDescription>{erreur}</AlertDescription>
          </Alert>
        )}
      </div>
    );
  }

  if (!question) return null;
  const affichee = retour?.question ?? question;
  const part = question.temps_ms > 0 ? restant / question.temps_ms : 0;
  const secondes = Math.ceil(restant / 1000);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between text-sm font-bold text-muted-foreground">
        <span>
          Question {question.rang} / {etat.total}
        </span>
        <span className="inline-flex items-center gap-1">
          <Timer aria-hidden className="size-4" /> <span aria-hidden>{secondes} s</span>
          <span className="sr-only">{secondes} secondes restantes</span>
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
      <h2
        ref={titre}
        tabIndex={-1}
        className="font-display text-2xl leading-snug text-ink outline-none"
      >
        <span className="sr-only">
          Question {question.rang} sur {etat.total} :{" "}
        </span>
        {affichee.enonce}
      </h2>
      <div className="grid gap-3">
        {affichee.choix.map((texte, i) => {
          const etatChoix = !retour
            ? "neutre"
            : i === retour.correction.choix_attendu
              ? "juste"
              : i === retour.correction.choix_joueur
                ? "faux"
                : "autre";
          return (
            <button
              key={`${etat.tentative_id}:${affichee.rang}:${i}`}
              type="button"
              disabled={enCours || restant === 0 || retour !== null}
              onClick={() => void repondre(question, i)}
              data-correction={etatChoix}
              className={`flex min-h-14 items-center gap-3 rounded-2xl px-4 py-3 text-left font-semibold shadow-sm ring-1 transition ${
                etatChoix === "juste"
                  ? "bg-primary text-primary-foreground ring-primary motion-safe:animate-clignote"
                  : etatChoix === "faux"
                    ? "bg-logo-red text-white ring-logo-red motion-safe:animate-clignote"
                    : etatChoix === "autre"
                      ? "bg-white text-ink opacity-50 ring-border"
                      : "bg-white text-ink ring-border hover:ring-primary disabled:opacity-60"
              }`}
            >
              <span
                className={`grid size-8 shrink-0 place-items-center rounded-full font-bold ${
                  etatChoix === "juste" || etatChoix === "faux"
                    ? "bg-white/25 text-white"
                    : "bg-mist text-logo-blue"
                }`}
              >
                {etatChoix === "juste" ? (
                  <Check aria-hidden className="size-4" />
                ) : etatChoix === "faux" ? (
                  <X aria-hidden className="size-4" />
                ) : (
                  LETTRES[i]
                )}
              </span>
              {texte}
            </button>
          );
        })}
      </div>
      <p role="status" aria-live="polite" className="min-h-6 text-center font-bold">
        {retour &&
          (retour.correction.juste ? (
            <span className="text-primary">Bonne réponse !</span>
          ) : (
            <span className="text-logo-red">
              {retour.correction.choix_joueur === null ? "Temps écoulé" : "Mauvaise réponse"} : la
              bonne réponse était « {affichee.choix[retour.correction.choix_attendu]} ».
            </span>
          ))}
      </p>
      {restant === 0 && !retour && (
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

// Le récapitulatif de fin de partie (quiz des jeux) : chaque question ratée, la réponse donnée et la bonne.
function Recapitulatif({ erreurs }: { erreurs: NonNullable<EtatPartie["resultat"]>["erreurs"] }) {
  if (!erreurs) return null;
  if (erreurs.length === 0)
    return <p className="font-semibold text-primary">Sans faute : aucune question ratée !</p>;
  return (
    <section aria-labelledby="titre-recap" className="text-left">
      <h3 id="titre-recap" className="text-lg font-extrabold text-ink">
        Tes erreurs ({erreurs.length}) et les bonnes réponses
      </h3>
      <ol className="mt-3 space-y-3">
        {erreurs.map((e) => (
          <li key={e.rang} className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-border">
            <p className="font-bold text-ink">
              {e.rang}. {e.enonce}
            </p>
            <p className="mt-2 flex items-start gap-2 text-sm font-semibold text-logo-red">
              <X aria-hidden className="mt-0.5 size-4 shrink-0" />
              {e.ta_reponse ? `Ta réponse : ${e.ta_reponse}` : "Pas de réponse à temps"}
            </p>
            <p className="mt-1 flex items-start gap-2 text-sm font-semibold text-primary">
              <Check aria-hidden className="mt-0.5 size-4 shrink-0" />
              Bonne réponse : {e.reponse_attendue}
            </p>
            {e.explication && (
              <p className="mt-2 text-sm font-medium text-ink/75">{e.explication}</p>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
