import { Link } from "@tanstack/react-router";
import { Hourglass, Loader2, Play, UserPlus } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { PartieQuiz } from "@/components/quiz/PartieQuiz";
import { Vies } from "@/components/quiz/Vies";
import { plusDeVies } from "@/lib/vies";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { useMoi } from "@/hooks/use-moi";
import {
  chargerQuiz,
  ErreurApi,
  lancerQuiz,
  lancerQuizOuvert,
  partieJoueur,
  partieSansCompte,
  type CatalogueQuiz,
  type EtatPartie,
  type QuizOuvert,
  type Vies as ViesDuJour,
} from "@/lib/api/client";
import { NIVEAUX_JEUX, nomNiveau, points } from "@/lib/bareme";
import { LANGUE_DE_BASE, langueCourante } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

export type Defi = { titre: string; numero: number; quiz: QuizOuvert };

// Spec 034 : le niveau du quiz et ce qu'il rapporte ; à défaut de niveau, le titre du quiz servi par l'API.
function descriptionDuDefi(defi: Defi) {
  const niveau = NIVEAUX_JEUX.find((n) => n.code === defi.quiz.niveau);
  // Hors du français, le titre servi par l'API (en français) cède la place à la mention générale.
  if (!niveau)
    return defi.quiz.titre === defi.titre || langueCourante() !== LANGUE_DE_BASE
      ? m.quiz_parcours_officiel()
      : defi.quiz.titre;
  return m.quiz_description_niveau({
    niveau: nomNiveau(niveau.code),
    points: points(niveau.eleve),
  });
}

// Le joueur sans compte a épuisé ses quiz d'essai : l'API le marque (X-Raison: fin-essai). Tout autre refus, même un
// 403 (contrôle d'origine, certification) ou un 429, garde le message de l'API : c'était le bug du 2026-11-10.
const estFinDEssai = (e: unknown) => e instanceof ErreurApi && e.raison === "fin-essai";

// Un compte connecté que l'API refuse de faire jouer (403) : équipe, compte à activer ou à vérifier.

export function FinDEssai() {
  return (
    <div className="space-y-5 py-4 text-center">
      <span className="mx-auto inline-flex size-14 items-center justify-center rounded-2xl bg-sun/30 text-ink">
        <Hourglass className="size-7" />
      </span>
      <p className="font-display text-2xl text-logo-blue">{m.quiz_essai_titre()}</p>
      <p className="mx-auto max-w-md font-semibold text-ink/80">{m.quiz_essai_texte()}</p>
      <div className="flex flex-wrap justify-center gap-3">
        <Button asChild className="btn-fx h-12 rounded-full px-6 font-bold">
          <Link to="/inscription">
            <UserPlus className="size-4" /> {m.quiz_creer_compte()}
          </Link>
        </Button>
        <Button asChild variant="outline" className="h-12 rounded-full px-6 font-bold">
          <Link to="/connexion">{m.quiz_deja_compte()}</Link>
        </Button>
      </div>
    </div>
  );
}

// Un défi du parcours officiel, joué dans une fenêtre (2026-11-10) : un compte connecté joue sa partie habituelle,
// un joueur sans compte joue à l'essai. Le serveur arbitre tout, y compris la limite d'essai.
export function DefiQuiz({
  defi,
  catalogue,
  onFermer,
}: {
  defi: Defi | null;
  catalogue: CatalogueQuiz;
  onFermer: () => void;
}) {
  const { data: moi } = useMoi();
  const connecte = catalogue.connecte || Boolean(moi);
  const [partie, setPartie] = useState<EtatPartie | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const [essaiFini, setEssaiFini] = useState(false);
  const [enCoursId, setEnCoursId] = useState<string | null>(null);
  const [interdit, setInterdit] = useState(false);
  const [verifie, setVerifie] = useState(false);
  const [vies, setVies] = useState<ViesDuJour | null>(null);
  // Le dernier défi reste affiché pendant l'animation de fermeture.
  const [affiche, setAffiche] = useState<Defi | null>(defi);
  // Chaque ouverture reçoit un numéro : une réponse arrivée après un changement de défi est ignorée.
  const ouverture = useRef(0);

  // Chaque défi ouvert repart de son écran d'accueil ; un compte connecté voit s'il a une partie à reprendre, ou
  // pourquoi il ne peut pas jouer.
  useEffect(() => {
    const numero = ++ouverture.current;
    if (!defi) return;
    setAffiche(defi);
    setPartie(null);
    setErreur(null);
    setEssaiFini(false);
    setEnCoursId(null);
    setInterdit(false);
    setEnCours(false);
    setVerifie(!connecte);
    setVies(null);
    if (!connecte) return;
    chargerQuiz()
      .then((liste) => {
        if (numero !== ouverture.current) return;
        setEnCoursId(liste.quiz.find((q) => q.id === defi.quiz.id)?.tentative_en_cours ?? null);
        setVies(liste.vies ?? null);
      })
      .catch((e: unknown) => {
        if (numero !== ouverture.current) return;
        if (e instanceof ErreurApi && e.statut === 403) {
          setInterdit(true);
        }
      })
      .finally(() => {
        if (numero === ouverture.current) setVerifie(true);
      });
  }, [defi, connecte]);

  const lancer = (id: string) => (connecte ? lancerQuiz(id) : lancerQuizOuvert(id));

  async function demarrer(action: () => Promise<EtatPartie>) {
    const numero = ouverture.current;
    setErreur(null);
    setEnCours(true);
    try {
      const etat = await action();
      if (numero === ouverture.current) setPartie(etat);
    } catch (e) {
      if (numero !== ouverture.current) return;
      if (!connecte && estFinDEssai(e)) setEssaiFini(true);
      else setErreur(e instanceof ErreurApi ? e.message : m.erreur_indisponible());
    } finally {
      if (numero === ouverture.current) setEnCours(false);
    }
  }

  // Pendant une question, un clic à côté ou la touche Échap ne ferme pas la fenêtre : seul le bouton le fait.
  const enJeu = partie !== null && partie.resultat === null;
  const retenir = (e: Event) => {
    if (enJeu) e.preventDefault();
  };

  return (
    <Dialog open={defi !== null} onOpenChange={(ouvert) => !ouvert && onFermer()}>
      <DialogContent
        onInteractOutside={retenir}
        onEscapeKeyDown={retenir}
        className="max-h-[100dvh] w-full max-w-2xl overflow-y-auto rounded-none p-5 sm:max-h-[92dvh] sm:rounded-[2rem] sm:p-8"
      >
        {affiche && (
          <>
            <header className="pr-8">
              <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
                <span className="h-1 w-8 rounded-full bg-primary" />
                {m.jeux_quiz_numero({ numero: String(affiche.numero).padStart(2, "0") })}
              </p>
              <DialogTitle className="mt-2 text-2xl leading-tight text-logo-blue md:text-3xl">
                {affiche.titre}
              </DialogTitle>
              <DialogDescription className="mt-1 text-sm font-semibold text-muted-foreground">
                {descriptionDuDefi(affiche)}
              </DialogDescription>
            </header>

            <div className="mt-6">
              {essaiFini ? (
                <FinDEssai />
              ) : interdit ? (
                <p className="rounded-2xl bg-sun/20 p-4 text-center font-semibold text-ink">
                  {moi?.role === "admin" ? m.quiz_equipe() : m.quiz_a_activer()}
                </p>
              ) : partie ? (
                <PartieQuiz
                  depart={partie}
                  appels={connecte ? partieJoueur : partieSansCompte}
                  avecPoints={moi?.role === "eleve"}
                  onRejouer={async () => {
                    try {
                      setPartie(await lancer(affiche.quiz.id));
                    } catch (e) {
                      if (!connecte && estFinDEssai(e)) setEssaiFini(true);
                      else throw e;
                    }
                  }}
                  actions={
                    <Button
                      variant="outline"
                      className="h-11 rounded-full px-5 font-bold"
                      onClick={onFermer}
                    >
                      {m.quiz_autres_defis()}
                    </Button>
                  }
                />
              ) : (
                <div className="space-y-4">
                  <ul className="list-disc space-y-1 pl-5 text-sm">
                    <li>
                      {m.quiz_regle_questions({
                        questions: String(catalogue.nb_questions),
                        secondes: String(Math.round(catalogue.temps_ms / 1000)),
                      })}
                    </li>
                    <li>{m.quiz_regle_temps()}</li>
                    <li>{m.quiz_regle_seuil({ seuil: String(catalogue.seuil) })}</li>
                    <li>{m.quiz_regle_fermer()}</li>
                  </ul>
                  <Vies vies={vies} />
                  {enCoursId && (
                    <p className="rounded-2xl bg-sun/20 p-3 text-sm font-semibold text-ink">
                      {m.quiz_partie_en_cours()}
                    </p>
                  )}
                  {erreur && (
                    <Alert variant="destructive">
                      <AlertDescription>{erreur}</AlertDescription>
                    </Alert>
                  )}
                  <div className="flex flex-wrap gap-3">
                    {enCoursId && (
                      <Button
                        className="h-12 rounded-full px-6 font-bold"
                        disabled={enCours}
                        onClick={() => void demarrer(() => partieJoueur.reprendre(enCoursId))}
                      >
                        <Play className="size-4" /> {m.quiz_reprendre_partie()}
                      </Button>
                    )}
                    <Button
                      variant={enCoursId ? "outline" : "default"}
                      className="btn-fx h-12 rounded-full px-6 font-bold"
                      disabled={enCours || !verifie || plusDeVies(vies)}
                      onClick={() => void demarrer(() => lancer(affiche.quiz.id))}
                    >
                      {enCours ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : (
                        <Play className="size-4" />
                      )}
                      {enCoursId ? m.quiz_recommencer() : m.quiz_commencer()}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
