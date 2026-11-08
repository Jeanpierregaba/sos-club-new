import { createFileRoute, Link, redirect, useRouter } from "@tanstack/react-router";
import { ArrowLeft, MessageCircle, Trash2 } from "lucide-react";
import { useState } from "react";

import { EtatContenu } from "@/components/articles/EtatContenu";
import { ServiceIndisponible } from "@/components/ServiceIndisponible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  chargerMesCommentaires,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  retirerCommentaire,
} from "@/lib/api/client";
import { dateCourte } from "@/lib/dates";

export const Route = createFileRoute("/_connecte/mes-commentaires")({
  gcTime: 0,
  beforeLoad: ({ context }) => {
    if (context.moi.role === "admin") throw redirect({ to: "/admin" });
  },
  loader: async () => {
    try {
      return { commentaires: (await chargerMesCommentaires()).commentaires, refus: null };
    } catch (e) {
      // Un encadreur pas encore vérifié : l'API refuse, la page l'explique.
      if (e instanceof ErreurApi && e.statut === 403) return { commentaires: [], refus: e.message };
      throw e;
    }
  },
  head: () => ({
    meta: [
      { title: "Mes commentaires — Club Santé SOS Docteur TV" },
      { name: "robots", content: "noindex" },
    ],
  }),
  errorComponent: ServiceIndisponible,
  component: MesCommentaires,
});

function MesCommentaires() {
  const { commentaires, refus } = Route.useLoaderData();
  const router = useRouter();
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState<string | null>(null);

  async function retirer(id: string) {
    if (!window.confirm("Retirer ce commentaire ? Il ne sera plus visible sur le site.")) return;
    setErreur(null);
    setEnCours(id);
    try {
      await retirerCommentaire(id);
      await router.invalidate();
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(null);
    }
  }

  return (
    <main className="min-h-screen bg-carnet px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-3xl">
        <Link
          to="/mon-espace"
          className="inline-flex items-center gap-2 text-sm font-bold text-logo-blue hover:underline"
        >
          <ArrowLeft className="size-4" /> Mon espace
        </Link>
        <p className="mt-4 flex items-center gap-3 text-sm font-extrabold uppercase tracking-widest text-logo-red">
          <span className="h-1 w-8 rounded-full bg-primary" />
          Réagir
        </p>
        <h1 className="mt-3 text-4xl leading-tight md:text-5xl">
          <span className="text-logo-blue">Mes</span>{" "}
          <span className="text-primary">commentaires</span>
        </h1>
        <p className="mt-4 max-w-2xl text-muted-foreground">
          Chaque commentaire est relu avant d'apparaître sous l'article : +5 points à sa première
          validation, pour 5 commentaires par jour au plus.
        </p>

        {erreur && (
          <Alert variant="destructive" className="mt-6">
            <AlertDescription>{erreur}</AlertDescription>
          </Alert>
        )}

        {refus ? (
          <p className="mt-8 rounded-3xl bg-card p-6 shadow-card">{refus}</p>
        ) : commentaires.length === 0 ? (
          <div className="mt-8 rounded-3xl bg-card p-8 text-center shadow-card">
            <MessageCircle className="mx-auto size-10 text-logo-blue/40" />
            <p className="mt-3 font-semibold">Tu n'as encore commenté aucun article.</p>
            <Link to="/articles" className="text-sm font-bold text-logo-blue hover:underline">
              Lire les articles
            </Link>
          </div>
        ) : (
          <ul className="mt-8 space-y-3">
            {commentaires.map((c) => (
              <li key={c.id} className="rounded-3xl bg-card p-5 shadow-card">
                <p className="text-sm text-muted-foreground">
                  Sur{" "}
                  {c.article.adresse ? (
                    <Link
                      to="/articles/$adresse"
                      params={{ adresse: c.article.adresse }}
                      className="font-bold text-logo-blue hover:underline"
                    >
                      {c.article.titre}
                    </Link>
                  ) : (
                    <strong>{c.article.titre}</strong>
                  )}{" "}
                  · envoyé le {dateCourte(c.cree_le)}
                </p>
                <p className="mt-2 whitespace-pre-line break-words text-ink">{c.texte}</p>
                <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                  <EtatContenu etat={c.etat} />
                  {(c.etat === "en_attente" || c.etat === "publie") && (
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={enCours === c.id}
                      onClick={() => void retirer(c.id)}
                      className="rounded-full text-xs font-bold text-logo-red"
                    >
                      <Trash2 className="size-3" /> Retirer
                    </Button>
                  )}
                </div>
                {c.motif && (
                  <p className="mt-3 rounded-2xl bg-logo-red/10 p-3 text-sm">
                    <strong>Motif :</strong> {c.motif}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
