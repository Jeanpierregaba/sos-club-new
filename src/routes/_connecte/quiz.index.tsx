import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { ArrowLeft, Brain, CheckCircle2, Play } from "lucide-react";

import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import {
  chargerAxes,
  chargerQuiz,
  ErreurApi,
  type AxePublic,
  type ListeQuiz,
} from "@/lib/api/client";

type Recherche = { axe?: string | undefined };

export const Route = createFileRoute("/_connecte/quiz/")({
  gcTime: 0,
  validateSearch: (search: Record<string, unknown>): Recherche =>
    typeof search["axe"] === "string" ? { axe: search["axe"] } : {},
  beforeLoad: ({ context }) => {
    if (context.moi.role === "admin") throw redirect({ to: "/admin/quiz" });
  },
  loaderDeps: ({ search }) => search,
  loader: async ({ deps }) => {
    try {
      const [liste, axes] = await Promise.all([
        chargerQuiz(deps.axe),
        chargerAxes().catch((): AxePublic[] => []),
      ]);
      return { liste, axes, refus: null };
    } catch (e) {
      // Un encadreur pas encore vérifié : l'API refuse, la page l'explique.
      if (e instanceof ErreurApi && e.statut === 403)
        return { liste: null as ListeQuiz | null, axes: [] as AxePublic[], refus: e.message };
      throw e;
    }
  },
  head: () => ({
    meta: [
      { title: "Quiz santé — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: PageQuiz,
});

function PageQuiz() {
  const { liste, axes, refus } = Route.useLoaderData();
  const { axe } = Route.useSearch();
  const libelle = (code: string) => axes.find((a) => a.code === code)?.libelle ?? code;
  // Sur la liste complète seulement : un filtre par axe fausserait le décompte.
  const joues = axe ? [] : (liste?.quiz.filter((q) => q.meilleur_score !== null) ?? []);

  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-4xl space-y-6">
        <Link
          to="/mon-espace"
          className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> Mon espace
        </Link>
        <header>
          <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
            <span className="h-1 w-8 rounded-full bg-primary" />
            Quiz santé
          </p>
          <h1 className="mt-3 text-4xl leading-tight md:text-5xl">
            <span className="text-logo-blue">Teste tes</span>{" "}
            <span className="text-primary">connaissances</span>
          </h1>
          {liste && (
            <p className="mt-3 max-w-2xl text-muted-foreground">
              {liste.nb_questions} questions tirées au hasard, quelques secondes pour chacune :
              réussis avec {liste.seuil} bonnes réponses. Un élève gagne des points la première fois
              qu'il réussit un quiz ; rejouer reste possible pour s'entraîner.
            </p>
          )}
        </header>

        {refus ? (
          <div className="rounded-3xl bg-card p-8 text-center shadow-card">
            <p className="font-semibold">{refus}</p>
          </div>
        ) : (
          liste && (
            <>
              {axes.length > 0 && (
                <nav aria-label="Filtrer par axe" className="flex flex-wrap gap-2">
                  <Filtre actif={!axe} libelle="Tous" />
                  {axes.map((a) => (
                    <Filtre key={a.code} code={a.code} actif={axe === a.code} libelle={a.libelle} />
                  ))}
                </nav>
              )}

              {joues.length > 0 && (
                <section className="rounded-3xl bg-card p-5 shadow-card sm:p-7">
                  <h2 className="font-display text-xl text-ink">Mes quiz</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {joues.filter((q) => q.reussi).length} réussi
                    {joues.filter((q) => q.reussi).length > 1 ? "s" : ""} sur {joues.length} joué
                    {joues.length > 1 ? "s" : ""}, parmi les quiz en ligne
                  </p>
                </section>
              )}

              {liste.quiz.length === 0 ? (
                <div className="rounded-3xl bg-card p-8 text-center shadow-card">
                  <Brain aria-hidden className="mx-auto size-10 text-logo-blue" />
                  <p className="mt-3 font-semibold">Aucun quiz en ligne pour l'instant.</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    L'équipe nationale prépare les premiers quiz : reviens bientôt.
                  </p>
                </div>
              ) : (
                <ul className="grid gap-4 sm:grid-cols-2">
                  {liste.quiz.map((q) => (
                    <li key={q.id} className="flex flex-col rounded-3xl bg-card p-5 shadow-card">
                      <div className="flex flex-wrap gap-2">
                        <span className="rounded-full bg-mist px-3 py-1 text-xs font-bold text-logo-blue">
                          {libelle(q.axe_code)}
                        </span>
                        {q.contenu_de_test && (
                          <span className="rounded-full bg-sun/30 px-3 py-1 text-xs font-bold text-ink">
                            Contenu de test
                          </span>
                        )}
                      </div>
                      <h2 className="mt-3 font-display text-xl text-ink">{q.titre}</h2>
                      {q.description && (
                        <p className="mt-1 text-sm text-muted-foreground">{q.description}</p>
                      )}
                      <p className="mt-3 text-sm font-semibold">
                        {q.reussi ? (
                          <span className="inline-flex items-center gap-1 text-primary">
                            <CheckCircle2 className="size-4" /> Réussi · meilleur score{" "}
                            {q.meilleur_score}/{liste.nb_questions}
                          </span>
                        ) : q.meilleur_score !== null ? (
                          <span className="text-muted-foreground">
                            Meilleur score {q.meilleur_score}/{liste.nb_questions}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">Pas encore joué</span>
                        )}
                      </p>
                      <div className="mt-auto flex items-center justify-between gap-3 pt-4">
                        <span className="text-xs text-muted-foreground">
                          {q.tentatives_restantes === null
                            ? "Parties sans limite"
                            : `${q.tentatives_restantes} partie${q.tentatives_restantes > 1 ? "s" : ""} possible${q.tentatives_restantes > 1 ? "s" : ""} aujourd'hui`}
                        </span>
                        {q.tentatives_restantes === null || q.tentatives_restantes > 0 ? (
                          <Link
                            to="/quiz/$id"
                            params={{ id: q.id }}
                            className="btn-fx inline-flex h-11 items-center gap-2 rounded-full bg-primary px-5 text-sm font-bold text-primary-foreground"
                          >
                            <Play className="size-4" /> Jouer
                          </Link>
                        ) : (
                          <span className="text-sm font-semibold text-muted-foreground">
                            Reviens demain
                          </span>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )
        )}
      </div>
    </main>
  );
}

function Filtre({ code, actif, libelle }: { code?: string; actif: boolean; libelle: string }) {
  return (
    <Link
      to="/quiz"
      search={code ? { axe: code } : {}}
      aria-current={actif ? "page" : undefined}
      className={`rounded-full px-3 py-1.5 text-sm font-semibold ring-1 transition ${
        actif ? "bg-primary text-primary-foreground ring-primary" : "bg-white ring-border"
      }`}
    >
      {libelle}
    </Link>
  );
}
