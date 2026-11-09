import { Loader2, Upload } from "lucide-react";
import { useId, useRef, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { ErreurApi, MESSAGE_INDISPONIBLE } from "@/lib/api/client";

// Dépôt d'un fichier de la bibliothèque (spec 028) : le choix lance l'envoi, une barre en suit la progression, et
// le refus de l'API (PDF piégé, image illisible, trop lourd) s'affiche tel quel.
export function DepotFichier({
  libelle,
  accept,
  aide,
  desactive = false,
  onEnvoie,
}: {
  libelle: string;
  accept: string;
  aide: string;
  desactive?: boolean;
  onEnvoie: (fichier: File, progression: (fraction: number) => void) => Promise<unknown>;
}) {
  const id = useId();
  const champ = useRef<HTMLInputElement>(null);
  const [progression, setProgression] = useState<number | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  async function envoyer(fichier: File) {
    setErreur(null);
    setProgression(0);
    try {
      await onEnvoie(fichier, setProgression);
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setProgression(null);
      if (champ.current) champ.current.value = "";
    }
  }

  const enCours = progression !== null;
  return (
    <div className="grid gap-2">
      <label
        htmlFor={id}
        className={`inline-flex w-fit cursor-pointer items-center gap-2 rounded-full px-4 py-2 text-sm font-bold ring-1 ring-border transition hover:bg-mist ${
          desactive || enCours ? "pointer-events-none opacity-60" : ""
        }`}
      >
        {enCours ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}
        {libelle}
      </label>
      <input
        ref={champ}
        id={id}
        type="file"
        accept={accept}
        className="sr-only"
        disabled={desactive || enCours}
        onChange={(e) => {
          const fichier = e.target.files?.[0];
          if (fichier) void envoyer(fichier);
        }}
      />
      <p className="text-xs text-muted-foreground">{aide}</p>
      {enCours && (
        <div
          role="progressbar"
          aria-label={`Envoi : ${libelle}`}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(progression * 100)}
          className="h-2 overflow-hidden rounded-full bg-muted"
        >
          <div
            className="h-full rounded-full bg-primary transition-[width]"
            style={{ width: `${Math.round(progression * 100)}%` }}
          />
        </div>
      )}
      {erreur && (
        <Alert variant="destructive">
          <AlertDescription>{erreur}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
