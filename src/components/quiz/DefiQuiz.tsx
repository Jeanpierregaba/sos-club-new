import { Link } from "@tanstack/react-router";
import { Hourglass, Loader2, Play, UserPlus } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { PartieQuiz } from "@/components/quiz/PartieQuiz";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { useMoi } from "@/hooks/use-moi";
import {
  chargerQuiz,
  ErreurApi,
  lancerQuiz,
  lancerQuizOuvert,
  MESSAGE_INDISPONIBLE,
  partieJoueur,
  partieSansCompte,
  type CatalogueQuiz,
  type EtatPartie,
  type QuizOuvert,
} from "@/lib/api/client";
import { NIVEAUX_JEUX, points } from "@/lib/bareme";

export type Defi = { titre: string; numero: number; quiz: QuizOuvert };

// Spec 034 : le niveau du quiz et ce qu'il rapporte ; à défaut de niveau, le titre du quiz servi par l'API.
function descriptionDuDefi(defi: Defi) {
  const niveau = NIVEAUX_JEUX.find((n) => n.code === defi.quiz.niveau);
  if (!niveau)
    return defi.quiz.titre === defi.titre ? "Quiz du parcours officiel" : defi.quiz.titre;
  return `Niveau ${niveau.nom} · ${points(niveau.eleve)} points à la première réussite pour un élève, la moitié pour son club s'il y est affilié`;
}

// Le joueur sans compte a épuisé ses quiz d'essai : l'API le marque (X-Raison: fin-essai). Tout autre refus, même un
// 403 (contrôle d'origine, certification) ou un 429, garde le message de l'API : c'était le bug du 2026-11-10.
const estFinDEssai = (e: unknown) => e instanceof ErreurApi && e.raison === "fin-essai";

// Un compte connecté que l'API refuse de faire jouer (403) : équipe, compte à activer ou à vérifier.
const MESSAGE_EQUIPE = "Les membres de l'équipe jouent en mode test, depuis l'espace admin.";
const MESSAGE_A_ACTIVER =
  "Ton compte ne peut pas encore jouer : confirme ton e-mail ou attends que l'équipe vérifie ton compte encadreur.";

export function FinDEssai() {
  return (
    <div className="space-y-5 py-4 text-center">
      <span className="mx-auto inline-flex size-14 items-center justify-center rounded-2xl bg-sun/30 text-ink">
        <Hourglass className="size-7" />
      </span>
      <p className="font-display text-2xl text-logo-blue">Ta période d'essai est terminée</p>
      <p className="mx-auto max-w-md font-semibold text-ink/80">
        Tu as déjà relevé tes défis d'essai. Crée ton compte gratuit pour continuer à relever tous
        les défis du parcours.
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        <Button asChild className="btn-fx h-12 rounded-full px-6 font-bold">
          <Link to="/inscription">
            <UserPlus className="size-4" /> Créer mon compte
          </Link>
        </Button>
        <Button asChild variant="outline" className="h-12 rounded-full px-6 font-bold">
          <Link to="/connexion">J'ai déjà un compte</Link>
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
    if (!connecte) return;
    chargerQuiz()
      .then((liste) => {
        if (numero !== ouverture.current) return;
        setEnCoursId(liste.quiz.find((q) => q.id === defi.quiz.id)?.tentative_en_cours ?? null);
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
      else setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
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
                Quiz {String(affiche.numero).padStart(2, "0")}
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
                  {moi?.role === "admin" ? MESSAGE_EQUIPE : MESSAGE_A_ACTIVER}
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
                      Autres défis
                    </Button>
                  }
                />
              ) : (
                <div className="space-y-4">
                  <ul className="list-disc space-y-1 pl-5 text-sm">
                    <li>
                      {catalogue.nb_questions} questions, une à la fois, avec{" "}
                      {Math.round(catalogue.temps_ms / 1000)} secondes pour chacune.
                    </li>
                    <li>Sans réponse à temps, la question compte comme ratée.</li>
                    <li>Il faut {catalogue.seuil} bonnes réponses pour réussir.</li>
                    <li>Si tu fermes la fenêtre, la question en cours est perdue.</li>
                  </ul>
                  {enCoursId && (
                    <p className="rounded-2xl bg-sun/20 p-3 text-sm font-semibold text-ink">
                      Tu as une partie en cours sur ce quiz : reprends-la, ou recommence (la partie
                      en cours sera close avec ton score actuel).
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
                        <Play className="size-4" /> Reprendre ma partie
                      </Button>
                    )}
                    <Button
                      variant={enCoursId ? "outline" : "default"}
                      className="btn-fx h-12 rounded-full px-6 font-bold"
                      disabled={enCours || !verifie}
                      onClick={() => void demarrer(() => lancer(affiche.quiz.id))}
                    >
                      {enCours ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : (
                        <Play className="size-4" />
                      )}
                      {enCoursId ? "Recommencer" : "Commencer"}
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
