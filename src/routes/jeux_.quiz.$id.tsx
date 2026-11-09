import { createFileRoute, Link, notFound, redirect } from "@tanstack/react-router";
import { ArrowLeft, Loader2, Lock, Play, UserPlus } from "lucide-react";
import { useState } from "react";

import { PartieQuiz } from "@/components/quiz/PartieQuiz";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  chargerCatalogueJeux,
  ErreurApi,
  lancerQuizOuvert,
  MESSAGE_INDISPONIBLE,
  partieSansCompte,
  type EtatPartie,
} from "@/lib/api/client";

// Jouer sans compte depuis la page des jeux (spec 031) : deux quiz au plus, sans points. Un compte connecté
// joue depuis ses quiz.
export const Route = createFileRoute("/jeux_/quiz/$id")({
  gcTime: 0,
  loader: async ({ params }) => {
    const catalogue = await chargerCatalogueJeux();
    if (catalogue.connecte) throw redirect({ to: "/quiz/$id", params: { id: params.id } });
    const quiz = catalogue.quiz.find((q) => q.id === params.id);
    if (!quiz) throw notFound();
    return { quiz, catalogue };
  },
  head: ({ loaderData }) => ({
    meta: [
      { title: `${loaderData?.quiz.titre ?? "Quiz"} — Quiz santé` },
      {
        name: "description",
        content: "Teste tes connaissances en santé : un quiz du Jeu Quiz Santé des Clubs Santé.",
      },
    ],
  }),
  errorComponent: ServiceIndisponible,
  notFoundComponent: () => (
    <main className="min-h-screen bg-carnet px-4 py-10">
      <p className="mx-auto max-w-xl rounded-3xl bg-card p-8 text-center font-semibold shadow-card">
        Ce quiz n'est pas en ligne.{" "}
        <a href="/jeux#jouer" className="text-logo-blue underline">
          Voir les quiz
        </a>
      </p>
    </main>
  ),
  component: QuizSansCompte,
});

function CreerUnCompte({ message }: { message: string }) {
  return (
    <div className="space-y-5 text-center">
      <span className="mx-auto inline-flex size-14 items-center justify-center rounded-2xl bg-sun/30 text-ink">
        <Lock className="size-7" />
      </span>
      <p className="text-lg font-bold text-ink">{message}</p>
      <div className="flex flex-wrap justify-center gap-3">
        <Button asChild className="btn-fx h-12 rounded-full px-6 font-bold">
          <Link to="/inscription" search={{ profil: "visiteur" }}>
            <UserPlus className="size-4" /> Créer mon compte visiteur
          </Link>
        </Button>
        <Button asChild variant="outline" className="h-12 rounded-full px-6 font-bold">
          <Link to="/connexion">J'ai déjà un compte</Link>
        </Button>
      </div>
    </div>
  );
}

function QuizSansCompte() {
  const { quiz, catalogue } = Route.useLoaderData();
  const [partie, setPartie] = useState<EtatPartie | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const [limite, setLimite] = useState<string | null>(null);

  async function demarrer() {
    setErreur(null);
    setEnCours(true);
    try {
      setPartie(await lancerQuizOuvert(quiz.id));
    } catch (e) {
      if (e instanceof ErreurApi && e.statut === 403) setLimite(e.message);
      else setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  }

  const restants = catalogue.restants ?? catalogue.limite;

  return (
    <>
      <SiteHeader />
      <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-2xl space-y-6">
          <a
            href="/jeux#jouer"
            className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
          >
            <ArrowLeft className="size-4" /> Tous les quiz
          </a>
          <header>
            <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
              <span className="h-1 w-8 rounded-full bg-primary" />
              Quiz santé
            </p>
            <h1 className="mt-3 text-3xl leading-tight text-logo-blue md:text-4xl">{quiz.titre}</h1>
          </header>

          <section className="rounded-3xl bg-card p-5 shadow-card sm:p-8">
            {limite ? (
              <CreerUnCompte message={limite} />
            ) : partie ? (
              <PartieQuiz
                depart={partie}
                appels={partieSansCompte}
                avecPoints={false}
                onRejouer={async () => {
                  try {
                    setPartie(await lancerQuizOuvert(quiz.id));
                  } catch (e) {
                    if (e instanceof ErreurApi && e.statut === 403) setLimite(e.message);
                    else throw e;
                  }
                }}
                actions={
                  <a
                    href="/jeux#jouer"
                    className="inline-flex h-11 items-center rounded-full px-5 text-sm font-bold text-logo-blue ring-1 ring-border hover:bg-mist"
                  >
                    Autres quiz
                  </a>
                }
              />
            ) : (
              <div className="space-y-4">
                {quiz.description && <p className="text-muted-foreground">{quiz.description}</p>}
                <ul className="list-disc space-y-1 pl-5 text-sm">
                  <li>
                    {catalogue.nb_questions} questions tirées au hasard, une à la fois, avec un
                    compte à rebours.
                  </li>
                  <li>Il faut {catalogue.seuil} bonnes réponses pour réussir.</li>
                  <li>
                    Sans compte, tu peux jouer à {catalogue.limite} quiz différents. Il t'en reste{" "}
                    <strong>{restants}</strong>. Ensuite, crée ton compte visiteur gratuit pour
                    continuer.
                  </li>
                </ul>
                {erreur && (
                  <Alert variant="destructive">
                    <AlertDescription>{erreur}</AlertDescription>
                  </Alert>
                )}
                <Button
                  className="btn-fx h-12 rounded-full px-6 font-bold"
                  disabled={enCours}
                  onClick={() => void demarrer()}
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
      <SiteFooter />
    </>
  );
}
