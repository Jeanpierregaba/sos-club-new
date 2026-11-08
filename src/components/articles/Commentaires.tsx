import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { Loader2, MessageCircle, Send } from "lucide-react";
import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useMoi } from "@/hooks/use-moi";
import {
  chargerCommentaires,
  chargerMesCommentaires,
  commenterArticle,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
} from "@/lib/api/client";
import { signer } from "@/lib/articles";
import { dateCourte } from "@/lib/dates";

export const LONGUEUR_MAX = 1000;
const CONFIRMATION = "Merci ! Ton commentaire sera visible après sa validation.";

// Les commentaires d'un article (spec 025). Le texte est affiché tel quel, jamais interprété : ni HTML, ni
// Markdown, ni lien. Un commentaire envoyé n'est visible que de son auteur jusqu'à l'approbation.
export function Commentaires({ adresse }: { adresse: string }) {
  const [page, setPage] = useState(1);
  const { data: moi } = useMoi();
  const peutCommenter = moi?.role === "eleve" || moi?.role === "encadreur";
  const publics = useQuery({
    queryKey: ["commentaires", adresse, page],
    queryFn: () => chargerCommentaires(adresse, page),
  });
  const miens = useQuery({
    queryKey: ["mes-commentaires", adresse],
    queryFn: () => chargerMesCommentaires(adresse),
    enabled: peutCommenter,
  });
  const enAttente = (miens.data?.commentaires ?? []).filter((c) => c.etat === "en_attente");
  const total = publics.data?.total ?? 0;

  return (
    <section aria-labelledby="commentaires" className="mt-14 border-t pt-10">
      <h2 id="commentaires" className="flex items-center gap-2 text-2xl text-logo-blue">
        <MessageCircle className="size-6" />
        Commentaires
        {total > 0 && <span className="text-base text-muted-foreground">({total})</span>}
      </h2>

      {publics.isError ? (
        <p className="mt-4 text-sm text-muted-foreground">
          Les commentaires ne sont pas disponibles pour le moment.
        </p>
      ) : publics.isPending ? (
        <Loader2
          className="mt-4 size-5 animate-spin text-muted-foreground"
          aria-label="Chargement"
        />
      ) : total === 0 ? (
        <p className="mt-4 text-sm text-muted-foreground">
          Personne n'a encore commenté cet article.
        </p>
      ) : (
        <ol className="mt-6 space-y-4">
          {publics.data.commentaires.map((c) => (
            <li key={c.id} className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-sm">
                <strong className="text-ink">{signer(c.signature)}</strong>
                <span className="text-muted-foreground"> · {dateCourte(c.publie_le)}</span>
              </p>
              <p className="mt-2 whitespace-pre-line break-words text-ink/90">{c.texte}</p>
            </li>
          ))}
        </ol>
      )}
      {publics.data && publics.data.pages > 1 && (
        <nav aria-label="Pages des commentaires" className="mt-4 flex items-center gap-3 text-sm">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            Précédents
          </Button>
          <span>
            Page {page} sur {publics.data.pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= publics.data.pages}
            onClick={() => setPage(page + 1)}
          >
            Suivants
          </Button>
        </nav>
      )}

      {enAttente.length > 0 && (
        <div className="mt-6 space-y-3">
          {enAttente.map((c) => (
            <div key={c.id} className="rounded-2xl border border-dashed bg-sun/10 p-4">
              <p className="text-xs font-bold text-ink/70">
                Ton commentaire · en attente de validation
              </p>
              <p className="mt-2 whitespace-pre-line break-words text-ink/80">{c.texte}</p>
            </div>
          ))}
        </div>
      )}

      {peutCommenter ? (
        <Formulaire adresse={adresse} />
      ) : moi ? null : (
        <p className="mt-6 rounded-2xl bg-mist p-4 text-sm">
          <Link to="/connexion" className="font-bold text-logo-blue hover:underline">
            Connecte-toi
          </Link>{" "}
          pour commenter cet article.
        </p>
      )}
    </section>
  );
}

function Formulaire({ adresse }: { adresse: string }) {
  const client = useQueryClient();
  const [texte, setTexte] = useState("");
  const [confirmation, setConfirmation] = useState(false);
  const envoi = useMutation({
    mutationFn: () => commenterArticle(adresse, texte),
    onSuccess: () => {
      setTexte("");
      setConfirmation(true);
      void client.invalidateQueries({ queryKey: ["mes-commentaires"] });
    },
  });
  const vide = texte.trim().length === 0;
  const erreur = envoi.error
    ? envoi.error instanceof ErreurApi
      ? envoi.error.message
      : MESSAGE_INDISPONIBLE
    : null;

  return (
    <form
      className="mt-6 space-y-3 rounded-2xl bg-white p-4 shadow-sm"
      onSubmit={(e) => {
        e.preventDefault();
        if (!vide && !envoi.isPending) envoi.mutate();
      }}
    >
      <Label htmlFor="commentaire">Ton commentaire</Label>
      <Textarea
        id="commentaire"
        value={texte}
        maxLength={LONGUEUR_MAX}
        rows={4}
        onChange={(e) => {
          setTexte(e.target.value);
          setConfirmation(false);
        }}
        placeholder="Partage ton avis ou ton expérience, avec respect."
      />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="text-xs text-muted-foreground">
          {texte.length} / {LONGUEUR_MAX} · visible après validation par l'équipe
        </span>
        <Button type="submit" className="rounded-full font-bold" disabled={vide || envoi.isPending}>
          {envoi.isPending ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Send className="size-4" />
          )}
          Envoyer
        </Button>
      </div>
      {confirmation && (
        <p role="status" className="text-sm font-semibold text-ink">
          {CONFIRMATION}
        </p>
      )}
      {erreur && (
        <Alert variant="destructive">
          <AlertDescription>{erreur}</AlertDescription>
        </Alert>
      )}
    </form>
  );
}
