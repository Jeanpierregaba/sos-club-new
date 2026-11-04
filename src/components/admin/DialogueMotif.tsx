import { Loader2 } from "lucide-react";
import { useState, type ReactNode } from "react";

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
import { Textarea } from "@/components/ui/textarea";
import { ErreurApi, MESSAGE_INDISPONIBLE } from "@/lib/api/client";

// Toute action sensible demande un motif : il est inscrit au journal d'audit.
export function DialogueMotif({
  ouvert,
  onOuvert,
  titre,
  description,
  bouton,
  danger = false,
  onConfirme,
}: {
  ouvert: boolean;
  onOuvert: (ouvert: boolean) => void;
  titre: string;
  description: ReactNode;
  bouton: string;
  danger?: boolean;
  onConfirme: (motif: string) => Promise<unknown>;
}) {
  const [motif, setMotif] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  const confirmer = async () => {
    if (motif.trim().length < 3) {
      setErreur("Indique un motif d'au moins 3 caractères.");
      return;
    }
    setErreur(null);
    setEnCours(true);
    try {
      await onConfirme(motif.trim());
      setMotif("");
      onOuvert(false);
    } catch (e) {
      setErreur(e instanceof ErreurApi ? e.message : MESSAGE_INDISPONIBLE);
    } finally {
      setEnCours(false);
    }
  };

  return (
    // Pas de fermeture pendant l'envoi : le résultat de l'action ne doit pas se perdre.
    <Dialog open={ouvert} onOpenChange={(o) => !enCours && onOuvert(o)}>
      <DialogContent className="rounded-3xl">
        <DialogHeader>
          <DialogTitle className="text-2xl text-logo-blue">{titre}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        {erreur && (
          <Alert variant="destructive">
            <AlertDescription>{erreur}</AlertDescription>
          </Alert>
        )}
        <label className="grid gap-1.5 text-sm font-bold">
          Motif (inscrit au journal)
          <Textarea
            value={motif}
            onChange={(e) => setMotif(e.target.value)}
            maxLength={500}
            rows={3}
            className="font-medium"
          />
        </label>
        <DialogFooter className="gap-2">
          <Button variant="outline" className="rounded-full" onClick={() => onOuvert(false)}>
            Annuler
          </Button>
          <Button
            onClick={confirmer}
            disabled={enCours}
            className={`rounded-full font-bold ${danger ? "bg-logo-red hover:bg-logo-red/90" : ""}`}
          >
            {enCours && <Loader2 className="size-4 animate-spin" />}
            {bouton}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
