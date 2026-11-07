import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { ArrowLeft, FileText, PenLine } from "lucide-react";

import { EtatContenu } from "@/components/articles/EtatContenu";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { chargerMesArticles, ErreurApi } from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";

export const Route = createFileRoute("/_connecte/mes-articles/")({
  gcTime: 0,
  beforeLoad: ({ context }) => {
    if (context.moi.role === "admin") throw redirect({ to: "/admin" });
  },
  loader: async () => {
    try {
      return { articles: (await chargerMesArticles()).articles, refus: null };
    } catch (e) {
      // Un encadreur pas encore vérifié : l'API refuse, la page l'explique.
      if (e instanceof ErreurApi && e.statut === 403) return { articles: [], refus: e.message };
      throw e;
    }
  },
  head: () => ({
    meta: [
      { title: "Mes articles — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: MesArticles,
});

function MesArticles() {
  const { articles, refus } = Route.useLoaderData();

  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-3xl">
        <Link
          to="/mon-espace"
          className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> Mon espace
        </Link>
        <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
              <span className="h-1 w-8 rounded-full bg-primary" />
              Publier
            </p>
            <h1 className="mt-3 text-4xl leading-tight md:text-5xl">
              <span className="text-logo-blue">Mes</span>{" "}
              <span className="text-primary">articles</span>
            </h1>
          </div>
          {!refus && (
            <Link
              to="/mes-articles/nouveau"
              className="btn-fx inline-flex h-12 items-center gap-2 rounded-full bg-primary px-6 font-bold text-primary-foreground shadow-lg"
            >
              <PenLine className="size-4" /> Écrire un article
            </Link>
          )}
        </div>
        <p className="mt-4 max-w-2xl text-muted-foreground">
          Raconte une action de ton club ou partage un sujet de santé. L'équipe nationale relit
          chaque article avant sa publication : +50 points à la première validation.
        </p>

        {refus ? (
          <p className="mt-8 rounded-3xl bg-card p-6 shadow-card">{refus}</p>
        ) : articles.length === 0 ? (
          <div className="mt-8 rounded-3xl bg-card p-8 text-center shadow-card">
            <FileText className="mx-auto size-10 text-logo-blue/40" />
            <p className="mt-3 font-semibold">Tu n'as encore écrit aucun article.</p>
            <p className="text-sm text-muted-foreground">Ton premier brouillon t'attend.</p>
          </div>
        ) : (
          <ul className="mt-8 space-y-3">
            {articles.map((a) => (
              <li key={a.id}>
                <Link
                  to="/mes-articles/$id"
                  params={{ id: a.id }}
                  className="block rounded-3xl bg-card p-5 shadow-card transition hover:-translate-y-0.5"
                >
                  <p className="font-display text-xl text-ink">{a.titre}</p>
                  <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                    <EtatContenu etat={a.etat} enLigne={a.en_ligne} />
                    <span>Modifié le {dateCourte(a.modifie_le)}</span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
