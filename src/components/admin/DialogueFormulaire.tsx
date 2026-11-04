import { Loader2 } from "lucide-react";
import { useState, type FormEvent, type ReactNode } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ErreurApi, MESSAGE_INDISPONIBLE } from "@/lib/api/client";

export const CHAMP_ADMIN =
  "h-11 w-full rounded-xl border bg-white px-3 text-sm font-semibold outline-none focus:border-logo-blue";

// Dialogue d'un formulaire de l'espace admin : il affiche le refus de l'API (doublon, version périmée, garde-fou)
// et ne se ferme qu'une fois l'enregistrement réussi.
export function DialogueFormulaire({
  ouvert,
  onOuvert,
  titre,
  description,
  bouton,
  danger = false,
  onEnvoie,
  children,
}: {
  ouvert: boolean;
  onOuvert: (ouvert: boolean) => void;
  titre: string;
  description?: ReactNode;
  bouton: string;
  danger?: boolean;
  onEnvoie: () => Promise<unknown>;
  children?: ReactNode;
}) {
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  const envoyer = async (e: FormEvent) => {
    e.preventDefault();
    setErreur(null);
    setEnCours(true);
    try {
      await onEnvoie();
      onOuvert(false);
    } catch (err) {
      setErreur(err instanceof ErreurApi ? err.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  };

  return (
    <Dialog
      open={ouvert}
      onOpenChange={(o) => {
        if (enCours) return;
        if (!o) setErreur(null);
        onOuvert(o);
      }}
    >
      <DialogContent className="max-h-[90vh] overflow-y-auto rounded-3xl">
        <form onSubmit={envoyer} className="grid gap-4">
          <DialogHeader>
            <DialogTitle className="text-2xl text-logo-blue">{titre}</DialogTitle>
            {description && <DialogDescription>{description}</DialogDescription>}
          </DialogHeader>
          {erreur && (
            <Alert variant="destructive" role="alert">
              <AlertDescription>{erreur}</AlertDescription>
            </Alert>
          )}
          {children}
          <DialogFooter className="gap-2">
            <Button
              type="button"
              variant="outline"
              className="rounded-full"
              disabled={enCours}
              onClick={() => onOuvert(false)}
            >
              Annuler
            </Button>
            <Button
              type="submit"
              disabled={enCours}
              className={`rounded-full font-bold ${danger ? "bg-logo-red hover:bg-logo-red/90" : ""}`}
            >
              {enCours && <Loader2 className="size-4 animate-spin" />}
              {bouton}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export function Champ({ libelle, children }: { libelle: string; children: ReactNode }) {
  return (
    <label className="grid gap-1.5 text-sm font-bold">
      {libelle}
      {children}
    </label>
  );
}

export function BadgeActif({ actif }: { actif: boolean }) {
  return actif ? null : (
    <span className="inline-flex items-center whitespace-nowrap rounded-full bg-logo-red/10 px-2.5 py-0.5 text-xs font-extrabold text-logo-red">
      Désactivé
    </span>
  );
}
