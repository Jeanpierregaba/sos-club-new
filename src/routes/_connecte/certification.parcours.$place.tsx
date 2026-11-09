import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { ArrowLeft, BookOpenText, Loader2, Play } from "lucide-react";
import { useState } from "react";

import { PartieQuiz } from "@/components/quiz/PartieQuiz";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  chargerMaCertification,
  ErreurApi,
  lancerQuiz,
  MESSAGE_INDISPONIBLE,
  partieJoueur,
  urlRessource,
  type EtatPartie,
} from "@/lib/api/client";
import { jouable } from "@/lib/certification";

export const Route = createFileRoute("/_connecte/certification/parcours/$place")({
  gcTime: 0,
  beforeLoad: ({ context }) => {
    if (context.moi.role === "admin") throw redirect({ to: "/admin/certification" });
    // La certification est réservée aux élèves et aux encadreurs (spec 030) : un visiteur joue aux quiz.
    if (context.moi.role === "visiteur") throw redirect({ to: "/quiz" });
  },
  // La partie ne commence qu'au clic : un chargement ou un préchargement ne consomme aucune tentative.
  loader: async ({ params }) => {
    let parcours;
    try {
      parcours = await chargerMaCertification();
    } catch (e) {
      if (e instanceof ErreurApi && e.statut === 403)
        throw redirect({ to: "/certification/parcours" });
      throw e;
    }
    const place = parcours.places.find((p) => String(p.place) === params.place);
    // Place inconnue, verrouillée ou sans quiz publié : retour au parcours, qui explique pourquoi.
    if (!place || !jouable(place) || !place.quiz_id)
      throw redirect({ to: "/certification/parcours" });
    return {
      place,
      quizId: place.quiz_id,
      nbQuestions: parcours.nb_questions,
      seuil: parcours.seuil,
    };
  },
  head: () => ({
    meta: [
      { title: "Quiz de certification — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: JouerPlace,
});

function JouerPlace() {
  const { place, quizId, nbQuestions, seuil } = Route.useLoaderData();
  const [partie, setPartie] = useState<EtatPartie | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const enCoursId = place.tentative_en_cours;

  async function demarrer(action: () => Promise<EtatPartie>) {
    setErreur(null);
    setEnCours(true);
    try {
      setPartie(await action());
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  }

  const retour = (
    <Link
      to="/certification/parcours"
      className="inline-flex h-11 items-center rounded-full px-5 text-sm font-bold text-logo-blue ring-1 ring-border hover:bg-mist"
    >
      Mon parcours
    </Link>
  );

  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-2xl space-y-6">
        <Link
          to="/certification/parcours"
          className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> Ma certification
        </Link>
        <header>
          <p className="flex flex-wrap items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
            <span className="h-1 w-8 rounded-full bg-primary" />
            Génie Imhotep · quiz {place.place} sur 12
            {place.contenu_de_test && (
              <span className="rounded-full bg-sun/30 px-2 py-0.5 text-xs normal-case tracking-normal text-ink">
                Contenu de test
              </span>
            )}
          </p>
          <h1 className="mt-3 break-words text-3xl leading-tight text-logo-blue md:text-4xl">
            {place.titre}
          </h1>
        </header>

        <section className="rounded-3xl bg-card p-5 shadow-card sm:p-8">
          {partie ? (
            <PartieQuiz
              depart={partie}
              appels={partieJoueur}
              // Un quiz du parcours ne rapporte pas de points : ce sont les badges et le certificat qui en donnent.
              avecPoints={false}
              onRejouer={async () => setPartie(await lancerQuiz(quizId))}
              actions={retour}
            />
          ) : (
            <div className="space-y-4">
              {place.description && <p className="text-muted-foreground">{place.description}</p>}
              {place.fascicule && (
                <a
                  href={urlRessource(place.fascicule.id)}
                  target="_blank"
                  rel="noopener"
                  className="flex items-center gap-3 rounded-2xl bg-mist p-4 font-bold text-logo-blue hover:underline"
                >
                  <BookOpenText aria-hidden className="size-5 shrink-0" />
                  <span>
                    Avant de jouer, lis le fascicule : {place.fascicule.titre}
                    <span className="sr-only"> (s'ouvre dans un nouvel onglet)</span>
                  </span>
                </a>
              )}
              <ul className="list-disc space-y-1 pl-5 text-sm">
                <li>{nbQuestions} questions, une à la fois, avec un compte à rebours.</li>
                <li>Sans réponse à temps, la question compte comme ratée.</li>
                <li>Il faut {seuil} bonnes réponses pour réussir ce quiz et ouvrir le suivant.</li>
                {place.tentatives_restantes !== null && (
                  <li>Parties restantes aujourd'hui sur ce quiz : {place.tentatives_restantes}.</li>
                )}
              </ul>
              {enCoursId && (
                <p className="rounded-2xl bg-sun/20 p-3 text-sm font-semibold text-ink">
                  Tu as une partie en cours sur ce quiz : reprends-la, ou recommence (la partie en
                  cours sera close avec ton score actuel).
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
                  className="h-12 rounded-full px-6 font-bold"
                  disabled={enCours}
                  onClick={() => void demarrer(() => lancerQuiz(quizId))}
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
        </section>
      </div>
    </main>
  );
}
