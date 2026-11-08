import { createFileRoute, Link, notFound, redirect } from "@tanstack/react-router";
import { ArrowLeft, Loader2, Play } from "lucide-react";
import { useState } from "react";

import { PartieQuiz } from "@/components/quiz/PartieQuiz";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  chargerQuiz,
  ErreurApi,
  lancerQuiz,
  MESSAGE_INDISPONIBLE,
  partieJoueur,
  type EtatPartie,
} from "@/lib/api/client";

export const Route = createFileRoute("/_connecte/quiz/$id")({
  gcTime: 0,
  beforeLoad: ({ context }) => {
    if (context.moi.role === "admin") throw redirect({ to: "/admin/quiz" });
  },
  // La partie ne commence qu'au clic : un chargement ou un préchargement ne consomme aucune tentative.
  loader: async ({ params }) => {
    let liste;
    try {
      liste = await chargerQuiz();
    } catch (e) {
      if (e instanceof ErreurApi && e.statut === 403) throw redirect({ to: "/quiz" });
      throw e;
    }
    const quiz = liste.quiz.find((q) => q.id === params.id);
    if (!quiz) throw notFound();
    return { quiz, nbQuestions: liste.nb_questions, seuil: liste.seuil };
  },
  head: () => ({
    meta: [{ title: "Quiz — Club Santé SOS Docteur TV" }, { name: "robots", content: "noindex" }],
  }),
  errorComponent: ServiceIndisponible,
  notFoundComponent: () => (
    <main className="min-h-screen bg-carnet px-4 py-10">
      <p className="mx-auto max-w-xl rounded-3xl bg-card p-8 text-center font-semibold shadow-card">
        Ce quiz n'est pas en ligne. <Link to="/quiz">Voir les quiz</Link>
      </p>
    </main>
  ),
  component: JouerQuiz,
});

function JouerQuiz() {
  const { quiz, nbQuestions, seuil } = Route.useLoaderData();
  const { moi } = Route.useRouteContext();
  const [partie, setPartie] = useState<EtatPartie | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);

  async function commencer() {
    setErreur(null);
    setEnCours(true);
    try {
      setPartie(await lancerQuiz(quiz.id));
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  }

  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-2xl space-y-6">
        <Link
          to="/quiz"
          className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> Tous les quiz
        </Link>
        <header>
          <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
            <span className="h-1 w-8 rounded-full bg-primary" />
            Quiz santé
            {quiz.contenu_de_test && (
              <span className="rounded-full bg-sun/30 px-2 py-0.5 text-xs normal-case tracking-normal text-ink">
                Contenu de test
              </span>
            )}
          </p>
          <h1 className="mt-3 text-3xl leading-tight text-logo-blue md:text-4xl">{quiz.titre}</h1>
        </header>

        <section className="rounded-3xl bg-card p-5 shadow-card sm:p-8">
          {partie ? (
            <PartieQuiz
              depart={partie}
              appels={partieJoueur}
              avecPoints={moi.role === "eleve"}
              onRejouer={commencer}
              actions={
                <Link
                  to="/quiz"
                  className="inline-flex h-11 items-center rounded-full px-5 text-sm font-bold text-logo-blue ring-1 ring-border hover:bg-mist"
                >
                  Autres quiz
                </Link>
              }
            />
          ) : (
            <div className="space-y-4">
              {quiz.description && <p className="text-muted-foreground">{quiz.description}</p>}
              <ul className="list-disc space-y-1 pl-5 text-sm">
                <li>{nbQuestions} questions, une à la fois, avec un compte à rebours.</li>
                <li>Sans réponse à temps, la question compte comme ratée.</li>
                <li>Il faut {seuil} bonnes réponses pour réussir.</li>
                <li>Si tu quittes la page, la question en cours est perdue.</li>
              </ul>
              {erreur && (
                <Alert variant="destructive">
                  <AlertDescription>{erreur}</AlertDescription>
                </Alert>
              )}
              <Button
                className="h-12 rounded-full px-6 font-bold"
                disabled={enCours}
                onClick={() => void commencer()}
              >
                {enCours ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Play className="size-4" />
                )}
                Commencer
              </Button>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
