import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Copy, Loader2, Send, Share2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useMoi } from "@/hooks/use-moi";
import {
  chargerEtatPartages,
  declarerPartage,
  ErreurApi,
  MESSAGE_INDISPONIBLE,
  type ReseauPartage,
} from "@/lib/api/client";
import { RESEAUX } from "@/lib/partages";

const CONFIRMATION =
  "Merci ! Ton partage sera vérifié par l'équipe ; tes points arrivent à la validation.";

// Partager un article publié (spec 044) : les liens de partage pour tout le monde, et pour un élève ou un encadreur
// connecté, la déclaration de sa publication. Les points ne viennent qu'après la vérification d'un modérateur.
export function PartagerArticle({ adresse, titre }: { adresse: string; titre: string }) {
  const { data: moi } = useMoi();
  const peutDeclarer = moi?.role === "eleve" || moi?.role === "encadreur";
  const [url, setUrl] = useState("");
  useEffect(() => setUrl(`${window.location.origin}/articles/${adresse}`), [adresse]);

  return (
    <section aria-labelledby="partager" className="mt-14 rounded-3xl bg-white p-6 shadow-sm">
      <h2 id="partager" className="flex items-center gap-2 text-2xl text-logo-blue">
        <Share2 className="size-6" />
        Partage cet article
      </h2>
      <LiensDePartage url={url} titre={titre} />
      {peutDeclarer && <Declaration adresse={adresse} />}
    </section>
  );
}

function LiensDePartage({ url, titre }: { url: string; titre: string }) {
  const [copie, setCopie] = useState(false);
  const lien = encodeURIComponent(url);
  const natif = typeof navigator !== "undefined" && typeof navigator.share === "function";
  const classe =
    "inline-flex h-10 items-center gap-2 rounded-full border bg-white px-4 text-sm font-bold transition hover:border-logo-blue/40";
  return (
    <div className="mt-4 flex flex-wrap gap-2">
      <a
        className={classe}
        href={`https://www.facebook.com/sharer/sharer.php?u=${lien}`}
        target="_blank"
        rel="noopener noreferrer"
      >
        Facebook
      </a>
      <a
        className={classe}
        href={`https://www.linkedin.com/sharing/share-offsite/?url=${lien}`}
        target="_blank"
        rel="noopener noreferrer"
      >
        LinkedIn
      </a>
      {/* Instagram et TikTok n'ont pas de partage par le web : on copie le lien pour le coller dans l'application. */}
      <button
        type="button"
        className={classe}
        onClick={() => {
          void navigator.clipboard?.writeText(url).then(() => setCopie(true));
        }}
      >
        {copie ? <Check className="size-4" /> : <Copy className="size-4" />}
        {copie ? "Lien copié" : "Copier le lien (Instagram, TikTok)"}
      </button>
      {natif && (
        <button
          type="button"
          className={classe}
          onClick={() => void navigator.share({ title: titre, url }).catch(() => undefined)}
        >
          <Share2 className="size-4" /> Partager…
        </button>
      )}
    </div>
  );
}

function Declaration({ adresse }: { adresse: string }) {
  const client = useQueryClient();
  const etat = useQuery({
    queryKey: ["partages-article", adresse],
    queryFn: () => chargerEtatPartages(adresse),
  });
  const [reseau, setReseau] = useState<ReseauPartage | "">("");
  const [lien, setLien] = useState("");
  const [confirme, setConfirme] = useState(false);
  const envoi = useMutation({
    mutationFn: () => declarerPartage(adresse, reseau as ReseauPartage, lien.trim()),
    onSuccess: async () => {
      setReseau("");
      setLien("");
      setConfirme(true);
      await client.invalidateQueries({ queryKey: ["partages-article", adresse] });
      await client.invalidateQueries({ queryKey: ["mes-partages"] });
    },
  });

  if (etat.isPending)
    return <Loader2 className="mt-4 size-5 animate-spin" aria-label="Chargement" />;
  if (etat.isError) {
    // Un encadreur pas encore vérifié : l'API refuse, on le lui explique.
    const refus = etat.error instanceof ErreurApi && etat.error.statut === 403;
    return (
      <p className="mt-4 rounded-2xl bg-mist p-4 text-sm">
        {refus
          ? etat.error.message
          : "La déclaration des partages n'est pas disponible pour le moment."}
      </p>
    );
  }
  const { nature, reseaux_declares: declares, restantes_aujourdhui: restantes, points } = etat.data;
  const republicationFaite = nature === "republication" && declares.length > 0;
  const libres = RESEAUX.filter((r) => !declares.includes(r.code));
  const erreur =
    envoi.error instanceof ErreurApi
      ? envoi.error.message
      : envoi.error
        ? MESSAGE_INDISPONIBLE
        : null;

  return (
    <div className="mt-6 border-t pt-5">
      <h3 className="font-display text-lg text-ink">J'ai partagé cet article</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        {nature === "partage"
          ? `C'est ton article : ${points ? `+${points} points` : "des points"} par réseau, une fois chacun, après vérification.`
          : `Relaie-le sur un réseau : ${points ? `+${points} points` : "des points"} une fois, après vérification.`}{" "}
        Colle le lien de ta publication : un simple clic sur un bouton ne suffit pas.
      </p>
      {confirme && (
        <p role="status" className="mt-3 rounded-2xl bg-leaf/10 p-3 text-sm font-semibold text-ink">
          {CONFIRMATION}
        </p>
      )}
      {republicationFaite ? (
        <p className="mt-3 text-sm font-semibold">
          Ta republication de cet article est déjà déclarée.
        </p>
      ) : libres.length === 0 ? (
        <p className="mt-3 text-sm font-semibold">
          Tu as déclaré ton article sur tous les réseaux.
        </p>
      ) : restantes === 0 ? (
        <p className="mt-3 text-sm font-semibold">
          Tu as atteint le nombre de déclarations possibles pour l'instant : 3 par jour, et 3 en
          attente de vérification à la fois. Reviens plus tard.
        </p>
      ) : (
        <form
          className="mt-4 grid gap-3 sm:grid-cols-[12rem_1fr_auto] sm:items-end"
          onSubmit={(e) => {
            e.preventDefault();
            setConfirme(false);
            envoi.mutate();
          }}
        >
          <div className="grid gap-1.5">
            <Label htmlFor="reseau-partage">Réseau</Label>
            <select
              id="reseau-partage"
              value={reseau}
              onChange={(e) => setReseau(e.target.value as ReseauPartage | "")}
              className="h-10 rounded-md border bg-white px-3 text-sm"
              required
            >
              <option value="">Choisis</option>
              {libres.map((r) => (
                <option key={r.code} value={r.code}>
                  {r.nom}
                </option>
              ))}
            </select>
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="lien-partage">Lien de ta publication</Label>
            <Input
              id="lien-partage"
              type="url"
              inputMode="url"
              placeholder="https://"
              maxLength={500}
              value={lien}
              onChange={(e) => setLien(e.target.value)}
              required
            />
          </div>
          <Button type="submit" disabled={!reseau || !lien.trim() || envoi.isPending}>
            {envoi.isPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Send className="size-4" />
            )}
            Déclarer
          </Button>
        </form>
      )}
      {erreur && (
        <p role="alert" className="mt-3 text-sm font-semibold text-destructive">
          {erreur}
        </p>
      )}
      {declares.length > 0 && nature === "partage" && (
        <p className="mt-3 text-xs text-muted-foreground">
          Déjà déclaré :{" "}
          {RESEAUX.filter((r) => declares.includes(r.code))
            .map((r) => r.nom)
            .join(", ")}
        </p>
      )}
    </div>
  );
}
